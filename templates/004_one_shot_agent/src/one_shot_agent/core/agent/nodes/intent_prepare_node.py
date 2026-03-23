"""
목적: 의도 분류 결과를 최종 응답 입력으로 정리하는 노드를 제공한다.
설명: 분류기 원문을 표준 의도 타입으로 정규화하고, 응답 프롬프트용 작업 지시문을 생성한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/one_shot_agent/core/agent/models/intent.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from one_shot_agent.core.agent.models import AgentIntentType
from one_shot_agent.shared.agent.nodes import function_node
from one_shot_agent.shared.logging import Logger, create_default_logger

_intent_prepare_logger: Logger = create_default_logger("IntentPrepareNode")


def _build_task_instruction(intent_type: AgentIntentType) -> str:
    """의도 타입별 최종 응답 지시문을 생성한다."""

    instruction_map = {
        AgentIntentType.SUMMARY: (
            "사용자 입력을 짧고 명확하게 요약하세요. 핵심 사항을 먼저 제시하고, "
            "불필요한 배경 설명은 줄이세요."
        ),
        AgentIntentType.TRANSLATION: (
            "사용자 입력을 자연스럽고 정확한 한국어 번역 결과로 제공하세요. "
            "번역문 외의 해설은 사용자가 요청한 경우에만 최소화하세요."
        ),
        AgentIntentType.FORMAT_WRITING: (
            "사용자가 원하는 목적과 형식을 만족하는 완성된 글을 바로 작성하세요. "
            "제목, 문단, 불릿 등 필요한 형식을 명확히 반영하세요."
        ),
        AgentIntentType.GENERAL: (
            "사용자 질문에 직접 답하세요. 장황한 서론 없이 핵심 내용을 먼저 제시하세요."
        ),
    }
    return instruction_map[intent_type]


def _run_intent_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """의도 분류 결과를 정규화해 후속 응답 노드 입력으로 변환한다."""

    intent_type = AgentIntentType.from_raw(state.get("intent_type_raw"))
    return {
        "intent_type": intent_type.value,
        "task_instruction": _build_task_instruction(intent_type),
    }


intent_prepare_node = function_node(
    fn=_run_intent_prepare_step,
    node_name="intent_prepare",
    logger=_intent_prepare_logger,
)

__all__ = ["intent_prepare_node"]
