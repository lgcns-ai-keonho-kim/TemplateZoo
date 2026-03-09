"""
목적: 스키마 선택 LLM 노드 조립체를 제공한다.
설명: Gemini 런타임 설정을 실행 시점에 읽어 스키마 선택 노드를 지연 초기화한다.
디자인 패턴: 모듈 조립 + 지연 초기화
참조: src/text_to_sql/core/chat/prompts/schema_selection_prompt.py
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from text_to_sql.core.chat.prompts import SCHEMA_SELECTION_PROMPT
from text_to_sql.integrations.llm import LLMClient
from text_to_sql.shared.chat.nodes import LLMNode, function_node
from text_to_sql.shared.exceptions import BaseAppException, ExceptionDetail
from text_to_sql.shared.logging import Logger, create_default_logger

_schema_selection_logger: Logger = create_default_logger("SchemaSelectionNode")
_schema_selection_node_instance: LLMNode | None = None


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


def _get_schema_selection_node() -> LLMNode:
    """스키마 선택 LLM 노드를 지연 초기화해 반환한다."""

    global _schema_selection_node_instance
    if _schema_selection_node_instance is not None:
        return _schema_selection_node_instance

    model_name, project = _require_gemini_runtime()
    model = ChatGoogleGenerativeAI(
        model=model_name,
        project=project,
        thinking_level="minimal",
    )
    llm_client = LLMClient(
        model=model,
        name="chat-schema-selection-llm",
    )
    _schema_selection_node_instance = LLMNode(
        llm_client=llm_client,
        node_name="schema_selection_llm",
        prompt=SCHEMA_SELECTION_PROMPT,
        output_key="schema_selection_raw",
        history_key="__skip_history__",
        stream_tokens=False,
        logger=_schema_selection_logger,
    )
    return _schema_selection_node_instance


def _run_schema_selection_step(state: Mapping[str, Any]) -> dict[str, str]:
    """지연 초기화된 스키마 선택 노드를 실행한다."""

    return _get_schema_selection_node().run(state)


schema_selection_node = function_node(
    fn=_run_schema_selection_step,
    node_name="schema_selection_llm",
    logger=_schema_selection_logger,
)

__all__ = ["schema_selection_node"]
