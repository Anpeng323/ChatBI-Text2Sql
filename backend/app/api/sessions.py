"""会话管理接口：列表 / 新建 / 删除 / 历史。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.models import SessionCreate, SessionInfo
from ..services.session_store import session_store

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionInfo])
async def list_sessions() -> list[SessionInfo]:
    return session_store.list()


@router.post("", response_model=SessionInfo)
async def create_session(body: SessionCreate | None = None) -> SessionInfo:
    title = body.title if body else None
    return session_store.create(title=title)


@router.get("/{session_id}")
async def get_session(session_id: str):
    sess = session_store.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="会话不存在")
    return sess


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    ok = session_store.delete(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"deleted": True}
