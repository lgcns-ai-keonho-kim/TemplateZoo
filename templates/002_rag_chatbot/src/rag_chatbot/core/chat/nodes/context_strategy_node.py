"""
목적: LLM 기반 컨텍스트 전략 분류 노드 조립체를 제공한다.
설명: 사용자 질문이 직전 assistant 답변만으로 처리 가능한지 분류해
      REUSE_LAST_ASSISTANT/USE_RAG 토큰을 반환한다.
디자인 패턴: 모듈 조립
참조: src/rag_chatbot/core/chat/nodes/context_strategy_route_node.py, src/rag_chatbot/shared/chat/nodes/llm_node.py
"""

from __future__ import annotations

import os
from enum import Enum

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from rag_chatbot.core.chat.prompts import CONTEXT_STRATEGY_PROMPT
from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.nodes import LLMNode
from rag_chatbot.shared.logging import Logger, create_default_logger


class ContextStrategy(str, Enum):
    """컨텍스트 전략 분류 결과 토큰."""

    REUSE_LAST_ASSISTANT = "REUSE_LAST_ASSISTANT"
    USE_RAG = "USE_RAG"


CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT = ContextStrategy.REUSE_LAST_ASSISTANT.value
CONTEXT_STRATEGY_USE_RAG = ContextStrategy.USE_RAG.value

_context_strategy_logger: Logger = create_default_logger("ContextStrategyNode")
_context_strategy_model = ChatOpenAI(
    model_name=os.getenv("OPENAI_MODEL", ""),
    openai_api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),
    reasoning_effort="minimal",
)
_context_strategy_llm_client = LLMClient(
    model=_context_strategy_model,
    name="chat-context-strategy-llm",
)

context_strategy_node = LLMNode(
    llm_client=_context_strategy_llm_client,
    node_name="context_strategy",
    prompt=CONTEXT_STRATEGY_PROMPT,
    output_key="context_strategy_raw",
    history_key="__skip_history__",
    stream_tokens=False,
    logger=_context_strategy_logger,
)

__all__ = [
    "ContextStrategy",
    "context_strategy_node",
    "CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT",
    "CONTEXT_STRATEGY_USE_RAG",
]
