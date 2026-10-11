"""SQL 安全校验器：确保 LLM 生成的 SQL 仅做只读查询，防止注入 / DDL / 误删。

策略：
- 仅允许单条 SELECT 语句（含 WITH 只读 CTE）。
- 禁止多语句、注释内藏语句、系统库访问。
- 强制追加 / 收紧 LIMIT，避免全表返回拖垮数据库。
- 配合连接层 MAX_EXECUTION_TIME 兜底超时。
"""
import re

_FORBIDDEN_KEYWORDS = (
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|RENAME|REPLACE|"
    r"GRANT|REVOKE|EXEC|EXECUTE|MERGE|LOAD|CALL|SET|USE|SHOW|DESCRIBE|"
    r"INTO\s+OUTFILE|INTO\s+DUMPFILE)\b"
)
# 系统库 / 信息库访问限制（平台定位为通用数据分析，不允许直接查元数据库）
_FORBIDDEN_DBS = (
    r"\b(information_schema|mysql|performance_schema|sys|"
    r"INFORMATION_SCHEMA|MYSQL|PERFORMANCE_SCHEMA|SYS)\b"
)
_MULTI_STMT = re.compile(r";\s*\S")
_COMMENT = re.compile(r"(--.*$)|(#.*$)|(/\*.*?\*/)", re.S | re.I)
_KEYWORD_RE = re.compile(_FORBIDDEN_KEYWORDS, re.I)
_DB_RE = re.compile(_FORBIDDEN_DBS)
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)(?:\s*,\s*(\d+))?", re.I)
_TRAILING_SEMICOLON = re.compile(r";\s*$")


class SQLValidationError(ValueError):
    """SQL 未通过安全校验时抛出。"""


def _strip_strings(sql: str) -> str:
    """去掉字符串字面量，避免关键字藏在字符串里蒙混过关。"""
    return re.sub(r"'[^']*'|\"[^\"]*\"|`[^`]*`", " ", sql)


def validate_sql(sql: str, max_limit: int = 1000) -> str:
    """校验并规范化 SQL，返回追加了 LIMIT 的安全语句。

    返回处理后的 SQL（强制 LIMIT 收紧到 max_limit 以内）。
    校验不通过抛出 SQLValidationError。
    """
    if not sql or not sql.strip():
        raise SQLValidationError("SQL 不能为空")

    cleaned = _COMMENT.sub(" ", sql)
    cleaned = cleaned.strip()
    if _TRAILING_SEMICOLON.search(cleaned + ";"):
        # 去掉尾部分号（仅允许做单语句判断）
        cleaned = _TRAILING_SEMICOLON.sub("", cleaned).strip()

    no_str = _strip_strings(cleaned)

    if _MULTI_STMT.search(cleaned.rstrip(";") + ";"):
        raise SQLValidationError("仅允许单条查询语句，检测到多条语句")

    if _KEYWORD_RE.search(no_str):
        raise SQLValidationError("仅允许只读 SELECT 查询，检测到危险关键字")

    if _DB_RE.search(no_str):
        raise SQLValidationError("不允许直接访问系统 / 元数据库")

    lowered = no_str.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise SQLValidationError("仅允许 SELECT / WITH 只读查询")

    # 强制 LIMIT 收紧
    m = _LIMIT_RE.search(cleaned)
    if m:
        if m.group(2):  # LIMIT offset, count
            count = int(m.group(2))
            new_limit = f"LIMIT {m.group(1)}, {min(count, max_limit)}"
        else:
            count = int(m.group(1))
            new_limit = f"LIMIT {min(count, max_limit)}"
        cleaned = _LIMIT_RE.sub(new_limit, cleaned)
    else:
        cleaned = f"{cleaned} LIMIT {max_limit}"

    return cleaned
