"""
목적: 컨텍스트 전략 분류 입력 준비 노드를 제공한다.
설명: 히스토리에서 직전 assistant 답변을 추출해 LLM 분류 입력 키(last_assistant_message)로 기록한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/core/chat/nodes/context_strategy_node.py, src/rag_chatbot/core/chat/models/entities.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rag_chatbot.core.chat.models import ChatMessage
from rag_chatbot.shared.chat.nodes import function_node
from rag_chatbot.shared.logging import Logger, create_default_logger

_context_strategy_prepare_logger: Logger = create_default_logger("ContextStrategyPrepareNode")


def _run_context_strategy_prepare_step(state: Mapping[str, Any]) -> dict[str, str]:
    """히스토리에서 직전 assistant 답변을 찾아 state에 기록한다."""

    history = state.get("history")
    last_assistant_message = ""
    if isinstance(history, list):
        for item in reversed(history):
            if not isinstance(item, ChatMessage):
                continue
            if item.role.value != "assistant":
                continue
            content = str(item.content or "").strip()
            if content:
                last_assistant_message = content
                break

    _context_strategy_prepare_logger.debug(
        "context.strategy.prepare: has_last_assistant=%s, last_assistant_length=%s"
        % (bool(last_assistant_message), len(last_assistant_message))
    )

    return {"last_assistant_message": last_assistant_message}


context_strategy_prepare_node = function_node(
    fn=_run_context_strategy_prepare_step,
    node_name="context_strategy_prepare",
    logger=_context_strategy_prepare_logger,
)

__all__ = ["context_strategy_prepare_node"]
