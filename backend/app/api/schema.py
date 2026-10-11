"""Schema 接口：返回自动探测到的表结构（供前端展示 / 调试）。"""
from __future__ import annotations

from fastapi import APIRouter

from ..db.mysql_adapter import MySQLAdapter
from ..db.schema_probe import describe_for_prompt, get_schema

router = APIRouter(prefix="/api", tags=["schema"])

_adapter = MySQLAdapter()


@router.get("/schema")
async def get_db_schema(force: bool = False) -> dict:
    data = get_schema(_adapter, force=force)
    return {"schema": data, "prompt_text": describe_for_prompt(data)}


@router.get("/health")
async def health() -> dict:
    return {"db": _adapter.health_check(), "status": "ok"}
