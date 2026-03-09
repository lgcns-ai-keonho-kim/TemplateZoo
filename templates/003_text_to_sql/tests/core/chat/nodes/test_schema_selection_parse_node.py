"""
목적: 스키마 선택 파서 노드를 검증한다.
설명: 쉼표 구분 alias 문자열을 유효 alias 목록으로 정규화하고 실패 상세를 남기는지 확인한다.
디자인 패턴: 노드 단위 테스트
참조: src/text_to_sql/core/chat/nodes/schema_selection_parse_node.py
"""

from __future__ import annotations

from text_to_sql.core.chat.nodes.schema_selection_parse_node import (
    _run_schema_selection_parse_step,
)


def test_schema_selection_parse_accepts_valid_aliases_only() -> None:
    """유효한 alias만 선택 결과에 남겨야 한다."""

    result = _run_schema_selection_parse_step(
        {
            "schema_selection_raw": "ecommerce, unknown, housing, ecommerce",
            "available_target_aliases": ["housing", "ecommerce"],
        }
    )

    assert result["selected_target_aliases"] == ["ecommerce", "housing"]
    assert result["sql_plan"]["selected_aliases"] == ["ecommerce", "housing"]
    assert result["sql_pipeline_failure_details"] == []


def test_schema_selection_parse_returns_failure_when_no_valid_alias_exists() -> None:
    """유효 alias가 없으면 selection 실패를 명시해야 한다."""

    result = _run_schema_selection_parse_step(
        {
            "schema_selection_raw": "unknown",
            "available_target_aliases": ["housing", "ecommerce"],
        }
    )

    assert result["selected_target_aliases"] == []
    assert result["sql_pipeline_failure_stage"] == "schema_selection"
    assert result["sql_pipeline_failure_details"][0]["code"] == "TARGET_ALIAS_SELECTION_EMPTY"
