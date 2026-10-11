"""exc_sql 工具：依赖注入 DatabaseAdapter，执行只读查询，结果暂存于 per-request holder。

设计要点：
- 工具本身只负责"执行 + 返回 markdown 表格 + 暴露结构化结果"，不做对话决策。
- 查询结果 DataFrame 暂存到调用方传入的 holder（per-request），彻底消除原 Demo 全局
  _LAST_DF 在并发/多会话下串数据的问题。
- SQL 校验在 adapter.execute_query 内完成（validate_sql）。
"""
from __future__ import annotations

import re

from langchain_core.tools import tool

import pandas as pd

from ..core.config import settings
from ..db.base import DatabaseAdapter


def make_exc_sql(adapter: DatabaseAdapter, holder: dict | None = None):
    """闭包工厂：绑定具体数据源与 per-request 结果容器，返回 LangChain @tool。"""
    max_rows = settings.max_result_rows

    @tool
    def exc_sql(sql_input: str) -> str:
        """对生成的 SQL 进行只读查询（MySQL）。返回查询结果的前 N 行 markdown 表格，
        并在末尾附上结构化 JSON（行数、列信息），供可视化与导出使用。

        Args:
            sql_input: 需要执行的 SELECT 查询语句。
        """
        try:
            df: pd.DataFrame = adapter.execute_query(sql_input)
        except Exception as e:  # 校验或执行错误原样回传，交由 LLM 修正
            msg = f"SQL执行出错: {e}\n请检查 SQL 语法或字段名后重试。"
            if holder is not None:
                holder["tool_md"] = msg
            return msg

        if holder is not None:
            holder["last_df"] = df
            holder["last_sql"] = sql_input
        n = len(df)
        if n == 0:
            # 明确告知"无数据"，避免模型把空结果误解为错误而编造数字
            msg = "查询结果：0 行（没有匹配的数据）。请如实告知用户当前查询条件下没有数据，不要编造任何数字。"
            if holder is not None:
                holder["tool_md"] = msg
            return msg
        preview = df.head(max_rows)
        try:
            md = preview.to_markdown(index=False)
        except Exception:
            # 兜底：极端环境下 to_markdown 依赖缺失时，用字符串表格替代
            md = preview.to_string(index=False)
        cols = [
            {"name": c, "dtype": str(t), "numeric": pd.api.types.is_numeric_dtype(df[c])}
            for c, t in df.dtypes.items()
        ]
        meta = (
            f"\n<!--RESULT_META "
            f'{{"rows":{n},"preview_rows":{len(preview)},"columns":{cols}}}-->'
        )
        full = f"{md}{meta}"
        if holder is not None:
            holder["tool_md"] = re.sub(r"<!--RESULT_META.*?-->", "", full).strip()
        return full

    return exc_sql
