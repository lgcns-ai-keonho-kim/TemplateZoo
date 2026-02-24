"""
목적: 컨텍스트 전략 분기 노드 조립체를 제공한다.
설명: LLM 원시 출력(context_strategy_raw)을 Enum 토큰으로 정규화해 context_strategy에 기록한다.
디자인 패턴: 모듈 조립
참조: src/rag_chatbot/core/chat/nodes/context_strategy_node.py, src/rag_chatbot/shared/chat/nodes/branch_node.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.nodes.context_strategy_node import (
    CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
    CONTEXT_STRATEGY_USE_RAG,
)
from rag_chatbot.shared.chat.nodes import BranchNode
from rag_chatbot.shared.logging import Logger, create_default_logger

_context_strategy_route_logger: Logger = create_default_logger("ContextStrategyRouteNode")

# NOTE:
# - selector_key: LLM 분류 원시 출력(state["context_strategy_raw"])을 읽는다.
# - branch_map: 정규화된 selector를 최종 전략 토큰으로 매핑한다.
# - default_branch/fallback_selector: 허용값이 아니면 보수적으로 USE_RAG를 사용한다.
context_strategy_route_node = BranchNode(
    selector_key="context_strategy_raw",
    branch_map={
        CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT: CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
        CONTEXT_STRATEGY_USE_RAG: CONTEXT_STRATEGY_USE_RAG,
    },
    default_branch=CONTEXT_STRATEGY_USE_RAG,
    output_key="context_strategy",
    normalize_case=True,
    allowed_selectors={
        CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
        CONTEXT_STRATEGY_USE_RAG,
    },
    fallback_selector=CONTEXT_STRATEGY_USE_RAG,
    logger=_context_strategy_route_logger,
)

__all__ = ["context_strategy_route_node"]
