"""
목적: LLM 기반 컨텍스트 전략 분류 노드 조립체를 제공한다.
설명: Gemini 런타임 설정을 실행 시점에 읽어 컨텍스트 전략 분류 노드를 지연 초기화한다.
디자인 패턴: 모듈 조립 + 지연 초기화
참조: src/text_to_sql/core/chat/prompts/context_strategy_prompt.py
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from enum import Enum
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from text_to_sql.core.chat.prompts import CONTEXT_STRATEGY_PROMPT
from text_to_sql.integrations.llm import LLMClient
from text_to_sql.shared.chat.nodes import LLMNode, function_node
from text_to_sql.shared.exceptions import BaseAppException, ExceptionDetail
from text_to_sql.shared.logging import Logger, create_default_logger


class ContextStrategy(str, Enum):
    """컨텍스트 전략 분류 결과 토큰."""

    REUSE_LAST_ASSISTANT = "REUSE_LAST_ASSISTANT"
    USE_METADATA = "USE_METADATA"
    USE_SQL = "USE_SQL"


CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT = ContextStrategy.REUSE_LAST_ASSISTANT.value
CONTEXT_STRATEGY_USE_METADATA = ContextStrategy.USE_METADATA.value
CONTEXT_STRATEGY_USE_SQL = ContextStrategy.USE_SQL.value

_context_strategy_logger: Logger = create_default_logger("ContextStrategyNode")
_context_strategy_node_instance: LLMNode | None = None


def _require_gemini_runtime() -> tuple[str, str]:
    """Gemini 필수 런타임 설정을 검증한다."""

    model = str(os.getenv("GEMINI_MODEL", "") or "").strip()
    project = str(os.getenv("GEMINI_PROJECT", "") or "").strip()
    if not model:
        detail = ExceptionDetail(
            code="GEMINI_MODEL_MISSING",
            cause="GEMINI_MODEL 환경 변수가 비어 있습니다.",
        )
        raise BaseAppException("Gemini 모델 설정이 필요합니다.", detail)
    if not project:
        detail = ExceptionDetail(
            code="GEMINI_PROJECT_MISSING",
            cause="GEMINI_PROJECT 환경 변수가 비어 있습니다.",
        )
        raise BaseAppException("Gemini 프로젝트 설정이 필요합니다.", detail)
    return model, project


def _get_context_strategy_node() -> LLMNode:
    """컨텍스트 전략 LLM 노드를 지연 초기화해 반환한다."""

    global _context_strategy_node_instance
    if _context_strategy_node_instance is not None:
        return _context_strategy_node_instance

    model_name, project = _require_gemini_runtime()
    model = ChatGoogleGenerativeAI(
        model=model_name,
        project=project,
        thinking_level="minimal",
    )
    llm_client = LLMClient(
        model=model,
        name="chat-context-strategy-llm",
    )
    _context_strategy_node_instance = LLMNode(
        llm_client=llm_client,
        node_name="context_strategy",
        prompt=CONTEXT_STRATEGY_PROMPT,
        output_key="context_strategy_raw",
        history_key="__skip_history__",
        stream_tokens=False,
        logger=_context_strategy_logger,
    )
    return _context_strategy_node_instance


def _run_context_strategy_step(state: Mapping[str, Any]) -> dict[str, str]:
    """지연 초기화된 컨텍스트 전략 노드를 실행한다."""

    return _get_context_strategy_node().run(state)


context_strategy_node = function_node(
    fn=_run_context_strategy_step,
    node_name="context_strategy",
    logger=_context_strategy_logger,
)

__all__ = [
    "ContextStrategy",
    "context_strategy_node",
    "CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT",
    "CONTEXT_STRATEGY_USE_METADATA",
    "CONTEXT_STRATEGY_USE_SQL",
]
