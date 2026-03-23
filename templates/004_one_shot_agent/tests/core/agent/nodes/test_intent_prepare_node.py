"""
목적: 의도 준비 노드 동작을 검증한다.
설명: 분류기 원문이 표준 의도 타입과 작업 지시문으로 정규화되는지 확인한다.
디자인 패턴: 단위 테스트
참조: src/one_shot_agent/core/agent/nodes/intent_prepare_node.py
"""

from __future__ import annotations

from one_shot_agent.core.agent.nodes.intent_prepare_node import (
    intent_prepare_node,
)


def test_intent_prepare_node_maps_translation_label() -> None:
    """번역 계열 라벨은 TRANSLATION 의도로 정규화되어야 한다."""

    result = intent_prepare_node.run(
        {
            "run_id": "run-1",
            "user_message": "이 문장을 한국어로 번역해줘.",
            "history": [],
            "intent_type_raw": "translate",
        }
    )

    assert result["intent_type"] == "TRANSLATION"
    assert "번역" in result["task_instruction"]


def test_intent_prepare_node_falls_back_to_general_for_unknown_label() -> None:
    """알 수 없는 라벨은 GENERAL 의도로 폴백되어야 한다."""

    result = intent_prepare_node.run(
        {
            "run_id": "run-2",
            "user_message": "오늘 해야 할 일을 정리해줘.",
            "history": [],
            "intent_type_raw": "unexpected_label",
        }
    )

    assert result["intent_type"] == "GENERAL"
    assert "직접 답" in result["task_instruction"]
