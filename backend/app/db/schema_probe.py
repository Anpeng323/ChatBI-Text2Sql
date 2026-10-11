"""Schema 探测缓存：对探测结果做进程内缓存，避免每次请求都读 information_schema。"""
from __future__ import annotations

import time

from .base import DatabaseAdapter

CACHE_TTL = 300  # 秒
_cache: dict[str, tuple[float, dict]] = {}


def get_schema(adapter: DatabaseAdapter, force: bool = False) -> dict:
    """返回 schema 描述（带 TTL 缓存，按适配器类名维度）。"""
    key = adapter.__class__.__name__
    now = time.time()
    if not force:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    data = adapter.probe_schema()
    _cache[key] = (now, data)
    return data


def describe_for_prompt(schema: dict) -> str:
    """把 schema JSON 转成注入提示词的人类可读文本。"""
    lines = ["以下是数据库当前的表结构（供你编写 SQL 参考）：", ""]
    for t in schema.get("tables", []):
        tcomment = f" -- {t['comment']}" if t.get("comment") else ""
        lines.append(f"表 {t['name']}{tcomment}")
        for c in t.get("columns", []):
            ccomment = f" -- {c['comment']}" if c.get("comment") else ""
            lines.append(f"  - {c['name']} {c['type']}{ccomment}")
        lines.append("")
    return "\n".join(lines)
