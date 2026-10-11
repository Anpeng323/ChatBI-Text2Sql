"""会话编排：组装上下文、跑 ReAct 图，以 SSE 事件流形式产出 sql/data/chart/answer。

通过 LangGraph 的 astream_events 真正流式输出：首个 token 延迟低，SQL 与
数据结果作为独立事件推送，最终回答逐 token 流出。
"""
from __future__ import annotations

import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..core.config import settings
from ..core.prompts import build_system_prompt
from ..db.mysql_adapter import MySQLAdapter
from ..llm.client import build_llm, build_lightweight_llm
from ..llm.graph import build_graph
from ..schemas.models import ChatRequest, ChatStreamEvent, sse_format
from langgraph.errors import GraphRecursionError
from ..tools.exc_sql import make_exc_sql
from .chart_service import build_echarts_option
from .session_store import session_store

# ---- 进程级单例资源（延迟初始化，避免无凭据/无 DB 时导入即报错）----
_ADAPTER: MySQLAdapter | None = None
_SYSTEM_PROMPT: str | None = None
_INSTANCE: "ChatOrchestrator | None" = None

THINK_RE = re.compile(r"<think>.*?</think>", re.S | re.I)


def _strip_think(text: str) -> str:
    return THINK_RE.sub("", text).strip() if text else ""


class ChatOrchestrator:
    def __init__(self) -> None:
        global _ADAPTER, _SYSTEM_PROMPT
        self.adapter = _ADAPTER or MySQLAdapter()
        _ADAPTER = self.adapter
        self.llm = build_llm()
        self.light_llm = build_lightweight_llm()
        self.system_prompt = build_system_prompt(self.adapter)

    def _build_graph(self, holder: dict):
        tool = make_exc_sql(self.adapter, holder=holder)
        llm_with_tools = self.llm.bind_tools([tool])
        # self.llm 未绑定工具，作为"综合"节点，保证工具调用后必定产出最终回答
        return build_graph(llm_with_tools, [tool], llm_plain=self.llm)

    def _history_to_messages(self, session_id: str, user_msg: str):
        msgs: list = [SystemMessage(content=self.system_prompt)]
        sess = session_store.get(session_id)
        if sess:
            for m in sess["messages"]:
                role = m.get("role")
                content = m.get("content", "")
                if not isinstance(content, str) or not content:
                    continue
                if role == "user":
                    msgs.append(HumanMessage(content=content))
                elif role == "assistant":
                    # 只取自然语言回答，不回灌 SQL/图表等结构化附件
                    msgs.append(AIMessage(content=content))
        msgs.append(HumanMessage(content=user_msg))
        return msgs

    async def stream(self, req: ChatRequest):
        holder: dict = {}
        graph = self._build_graph(holder)
        msgs = self._history_to_messages(req.session_id, req.message)

        yield sse_format(ChatStreamEvent(type="thinking", payload={"text": "正在分析并查询数据库…"}))

        final_text = ""
        sql_emitted = False
        data_emitted = False
        import sys as _sys
        _seen_events = set()
        try:
            async for event in graph.astream_events(
                {"messages": msgs}, version="v2", config={"recursion_limit": 6}
            ):
                name = event.get("event")
                _seen_events.add(name)
                if name == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    # 工具调用片段：抓取 SQL 并单独推送（带"由工具查询"可信度标记）
                    if getattr(chunk, "tool_call_chunks", None):
                        for tc in chunk.tool_call_chunks:
                            arg = (tc or {}).get("args")
                            if arg and "SELECT" in arg.upper() and not sql_emitted:
                                sql_emitted = True
                                yield sse_format(
                                    ChatStreamEvent(
                                        type="sql",
                                        payload={"sql": arg, "verified": True,
                                                 "note": "由工具执行查询"},
                                    )
                                )
                    # 最终文本片段
                    if isinstance(chunk.content, str) and chunk.content:
                        piece = _strip_think(chunk.content)
                        if piece:
                            final_text += piece
                            yield sse_format(
                                ChatStreamEvent(type="answer", payload={"delta": piece})
                            )
                elif name == "on_tool_start":
                    inp = event["data"].get("input")
                    if isinstance(inp, str) and "SELECT" in inp.upper() and not sql_emitted:
                        sql_emitted = True
                        yield sse_format(
                            ChatStreamEvent(
                                type="sql",
                                payload={"sql": inp, "verified": True,
                                         "note": "由工具执行查询"},
                            )
                        )
                elif name == "on_tool_end":
                    out = event["data"].get("output")
                    if out is None:
                        continue
                    md = out.content if hasattr(out, "content") else str(out)
                    md_clean = re.sub(r"<!--RESULT_META.*?-->", "", md).strip()
                    holder["tool_md"] = md_clean
                    if not data_emitted and md_clean:
                        data_emitted = True
                        yield sse_format(
                            ChatStreamEvent(type="data", payload={"markdown": md_clean})
                        )
        except GraphRecursionError:
            # 工具持续出错导致超过递归上限：如实告知，避免前端长时间挂起
            yield sse_format(
                ChatStreamEvent(
                    type="error",
                    payload={"message": "查询多次尝试仍失败，请检查问题中的字段名/表名或换一种问法。"},
                )
            )
            print("[chat_service] GraphRecursionError：工具持续出错", file=_sys.stderr)
        finally:
            print("[chat_service] astream event names:", sorted(_seen_events), file=_sys.stderr)

        # 兜底：若工具节点事件未被 astream 暴露，但确有查询结果，补发 data 事件
        if not data_emitted and holder.get("tool_md"):
            yield sse_format(
                ChatStreamEvent(type="data", payload={"markdown": holder["tool_md"]})
            )

        if not final_text:
            final_text = "（抱歉，未能生成回答）"

        # 图表：基于本次查询的 DataFrame（per-request，无并发串数据）
        df = holder.get("last_df")
        if df is not None and not df.empty:
            option = build_echarts_option(df)
            if option:
                yield sse_format(
                    ChatStreamEvent(type="chart", payload={"option": option})
                )

        # 追问引导
        suggestions = self._gen_suggestions(req.message, final_text)
        yield sse_format(
            ChatStreamEvent(type="suggestions", payload={"items": suggestions})
        )

        # 持久化到会话（仅存自然语言回答 + 摘要附件）
        session_store.append(req.session_id, "user", req.message)
        session_store.append(
            req.session_id,
            "assistant",
            final_text,
            extra={
                "sql": holder.get("last_sql"),
                "chart": build_echarts_option(df) if df is not None and not df.empty else None,
            },
        )

        yield sse_format(ChatStreamEvent(type="done", payload={}))

    def _gen_suggestions(self, user_q: str, bot_a: str, k: int = 3) -> list[str]:
        try:
            resp = self.light_llm.invoke(
                [
                    SystemMessage(
                        content=(
                            "你是数据分析助手的追问引导模块。基于用户问题与助手回答，"
                            "生成 3 个用户最可能继续追问的、简短具体的问题（每题不超过 20 字）。"
                            "要求：每行一个，不要编号、不要引号、不要解释，只输出问题本身。"
                        )
                    ),
                    HumanMessage(content=f"用户问题：{user_q}\n助手回答：{bot_a}"),
                ]
            )
            items = [
                ln.strip(" \t\"'。.、")
                for ln in _strip_think(resp.content).splitlines()
                if ln.strip()
            ]
            items = [it for it in items if it][:k]
            if items:
                return items
        except Exception:
            pass
        return [
            "各月销量趋势如何",
            "不同渠道对比",
            "热门 SKU 排名",
        ]


def get_orchestrator() -> ChatOrchestrator:
    """延迟单例：首次调用时才创建（需要 API Key 与数据库）。"""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ChatOrchestrator()
    return _INSTANCE
