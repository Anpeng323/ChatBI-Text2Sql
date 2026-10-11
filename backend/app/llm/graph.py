"""LangGraph ReAct 编排：agent 节点 ↔ tools 节点，标准工具调用循环。

与具体数据源 / 工具解耦：工具通过参数注入，便于测试与扩展。
"""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _call_model(llm_with_tools):
    def call_model(state: State) -> dict:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    return call_model


def _after_tool(state: State) -> str:
    """工具执行后路由：出错则回到 agent 自动修正一次；成功则进入综合节点。

    成功分支进入无工具的 synthesize，模型无法再调用工具，故不会陷入递归；
    仅"持续出错"才会回到 agent，由 chat_service 的 recursion_limit 兜底。
    """
    last = state["messages"][-1]
    if isinstance(last, ToolMessage) and str(last.content).startswith("SQL执行出错"):
        return "agent"
    return "synthesize"


def build_graph(llm_with_tools, tools: list, llm_plain=None) -> "object":
    """构建并编译 ReAct 图。

    llm_plain 不绑定工具，用于"工具执行后强制综合"节点：保证工具成功后必定
    产出最终回答（模型此时无工具可调，避免反复调用工具陷入递归）。
    """
    graph = StateGraph(State)
    graph.add_node("agent", _call_model(llm_with_tools))
    graph.add_node("tools", ToolNode(tools))
    if llm_plain is not None:
        graph.add_node("synthesize", _call_model(llm_plain))
        graph.add_conditional_edges("agent", tools_condition)
        graph.add_conditional_edges("tools", _after_tool)
        graph.add_edge("synthesize", END)
    else:
        graph.add_conditional_edges("agent", tools_condition)
        graph.add_edge("tools", "agent")
    graph.set_entry_point("agent")
    return graph.compile()
