"""请求 / 响应与 SSE 事件的数据模型。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="会话 ID，用于历史隔离")
    message: str = Field(..., min_length=1, description="用户自然语言问题")
    stream: bool = True


class SessionCreate(BaseModel):
    title: str | None = None


class SessionInfo(BaseModel):
    session_id: str
    title: str
    created_at: float
    updated_at: float
    message_count: int


class ChatStreamEvent(BaseModel):
    """SSE 事件统一结构。

    type 取值：
      thinking  思考/状态占位
      sql       模型生成的 SQL（含"由工具查询"可信度标记）
      data      查询结果 markdown
      chart     ECharts option JSON
      answer    最终回答文本片段（流式）
      suggestions 追问列表
      error     错误信息
      done      结束
    """

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


def sse_format(event: ChatStreamEvent) -> str:
    """把事件序列化为 SSE 文本。"""
    import json

    return f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"
