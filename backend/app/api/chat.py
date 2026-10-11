"""对话接口：POST /api/chat，SSE 流式返回。"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..schemas.models import ChatRequest
from ..services.chat_service import get_orchestrator
from ..services.session_store import session_store

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    # 会话不存在则以传入 id 自动创建，保证历史隔离可用
    if not session_store.get(req.session_id):
        session_store.create(session_id=req.session_id)
    return StreamingResponse(
        get_orchestrator().stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
