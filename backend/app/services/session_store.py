"""会话历史存储：进程内内存字典，可平滑替换为 Redis。

每条消息形如 {"role": "user"|"assistant"|"system", "content": str}；
助手消息可能携带结构化附件（sql/data/chart）以 dict 形式存放。
"""
from __future__ import annotations

import time
import uuid

from ..schemas.models import SessionInfo


class Message(dict):
    pass


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def create(self, title: str | None = None, session_id: str | None = None) -> SessionInfo:
        sid = session_id or uuid.uuid4().hex
        now = time.time()
        self._sessions[sid] = {
            "session_id": sid,
            "title": title or "新会话",
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        return self._to_info(sid)

    def get(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)

    def list(self) -> list[SessionInfo]:
        return [
            self._to_info(sid)
            for sid, s in sorted(
                self._sessions.items(), key=lambda kv: kv[1]["updated_at"], reverse=True
            )
        ]

    def append(self, session_id: str, role: str, content: str, extra: dict | None = None) -> None:
        sess = self._sessions.get(session_id)
        if not sess:
            return
        msg: dict = {"role": role, "content": content}
        if extra:
            msg.update(extra)
        sess["messages"].append(msg)
        sess["updated_at"] = time.time()
        if sess["title"] == "新会话" and role == "user":
            sess["title"] = content[:20]

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def _to_info(self, session_id: str) -> SessionInfo:
        s = self._sessions[session_id]
        return SessionInfo(
            session_id=s["session_id"],
            title=s["title"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=len(s["messages"]),
        )


# 应用级单例
session_store = SessionStore()
