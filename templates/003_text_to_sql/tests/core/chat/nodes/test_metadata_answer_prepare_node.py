"""
목적: 메타데이터 기반 답변 준비 노드를 검증한다.
설명: answer_source_meta가 충분할 때는 설명 컨텍스트를 만들고, 부족할 때는 SQL 재실행 경로로 전환하는지 확인한다.
디자인 패턴: 노드 단위 테스트
참조: src/text_to_sql/core/chat/nodes/metadata_answer_prepare_node.py
"""

from __future__ import annotations

from text_to_sql.core.chat.nodes.metadata_answer_prepare_node import (
    _run_metadata_answer_prepare_step,
)


def test_metadata_answer_prepare_builds_description_context() -> None:
    """설명 가능한 컬럼이 있으면 응답 컨텍스트를 생성해야 한다."""

    result = _run_metadata_answer_prepare_step(
        {
            "user_message": "방금 결과에서 MEDV 값이 무슨 의미인지 설명해줘.",
            "answer_source_meta": {
                "table_ids": ["housing.boston_housing_price"],
                "column_ids": [
                    "housing.boston_housing_price.MEDV",
                    "MEDV",
                ],
                "column_descriptions": {
                    "housing.boston_housing_price.MEDV": "보스턴 주택 가격 지표",
                    "MEDV": "보스턴 주택 가격 지표",
                },
                "lineage": {
                    "housing.boston_housing_price.MEDV": "MEDV",
                    "MEDV": "MEDV",
                },
            },
        }
    )

    assert result["metadata_route"] == "response"
    assert "MEDV" in str(result["sql_answer_context"])
    assert result["sql_pipeline_failure_details"] == []


def test_metadata_answer_prepare_falls_back_to_sql_when_description_missing() -> None:
    """설명 가능한 컬럼이 없으면 SQL 재실행 경로로 전환해야 한다."""

    result = _run_metadata_answer_prepare_step(
        {
            "user_message": "방금 결과에서 MEDV 값이 무슨 의미인지 설명해줘.",
            "answer_source_meta": {
                "table_ids": ["housing.boston_housing_price"],
                "column_ids": [],
                "column_descriptions": {},
                "lineage": {},
            },
        }
    )

    assert result["metadata_route"] == "sql"
    assert result["sql_answer_context"] == ""
