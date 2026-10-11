"""MiniMax 模型客户端封装（OpenAI 兼容接口）。"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from ..core.config import settings

# MiniMax 的流式 usage 字段命名与 langchain-openai 预期不一致，
# 会触发 _create_usage_metadata 的 TypeError 并中断整个回答流。
# 包裹该函数：解析失败则降级为 None（仅丢失用量统计，不影响回答）。
import langchain_openai.chat_models.base as _lcob

_orig_create_usage_metadata = _lcob._create_usage_metadata


def _safe_create_usage_metadata(token_usage):
    try:
        return _orig_create_usage_metadata(token_usage)
    except Exception:
        return None


_lcob._create_usage_metadata = _safe_create_usage_metadata


def build_llm() -> ChatOpenAI:
    """构建 MiniMax ChatOpenAI 客户端。"""
    if not settings.minimax_api_key:
        raise RuntimeError(
            "未设置 MINIMAX_API_KEY，请在 .env 或环境变量中填写 MiniMax 的 API Key"
        )
    return ChatOpenAI(
        model=settings.minimax_model,
        api_key=settings.minimax_api_key,
        base_url=settings.minimax_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        max_retries=settings.llm_max_retries,
        timeout=settings.llm_timeout,
        # MiniMax 的流式 usage 字段命名与 langchain-openai 预期不一致，
        # 会引发 _create_usage_metadata 的 TypeError；关闭 usage 流式解析以规避。
        stream_usage=False,
    )


def build_lightweight_llm() -> ChatOpenAI:
    """用于追问生成等轻量任务，降低 max_tokens 省成本。"""
    llm = build_llm()
    llm.max_tokens = 256
    return llm
