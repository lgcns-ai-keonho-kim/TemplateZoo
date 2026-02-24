"""
목적: 컨텍스트 전략 후처리 노드를 제공한다.
설명: 정규화된 context_strategy를 기준으로 rag_context/rag_references를 세팅한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/core/chat/nodes/context_strategy_route_node.py, src/rag_chatbot/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rag_chatbot.core.chat.nodes.context_strategy_node import (
    CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
    CONTEXT_STRATEGY_USE_RAG,
)
from rag_chatbot.shared.chat.nodes import function_node
from rag_chatbot.shared.logging import Logger, create_default_logger

_context_strategy_finalize_logger: Logger = create_default_logger("ContextStrategyFinalizeNode")


def _run_context_strategy_finalize_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """최종 전략을 확정하고 response/RAG 노드가 사용할 컨텍스트를 준비한다."""

    strategy = str(state.get("context_strategy") or CONTEXT_STRATEGY_USE_RAG).strip().upper()
    last_assistant_message = str(state.get("last_assistant_message") or "").strip()
    reason = "use_rag"

    if strategy not in {
        CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
        CONTEXT_STRATEGY_USE_RAG,
    }:
        strategy = CONTEXT_STRATEGY_USE_RAG
        reason = "invalid_strategy_token"

    # 직전 assistant 답변이 없으면 재사용할 근거가 없으므로 강제로 USE_RAG를 사용한다.
    if not last_assistant_message:
        strategy = CONTEXT_STRATEGY_USE_RAG
        reason = "no_last_assistant"
    elif strategy == CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT:
        reason = "reuse_last_assistant"

    _context_strategy_finalize_logger.debug(
        "context.strategy.finalize: strategy=%s, reason=%s" % (strategy, reason)
    )

    return {
        "context_strategy": strategy,
        "rag_context": (
            last_assistant_message
            if strategy == CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT
            else ""
        ),
        "rag_references": [],
    }


context_strategy_finalize_node = function_node(
    fn=_run_context_strategy_finalize_step,
    node_name="context_strategy_finalize",
    logger=_context_strategy_finalize_logger,
)

__all__ = ["context_strategy_finalize_node"]
