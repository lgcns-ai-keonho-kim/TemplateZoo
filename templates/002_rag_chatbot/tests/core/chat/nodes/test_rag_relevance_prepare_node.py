"""
목적: RAG 관련성 prepare 노드 동작을 검증한다.
설명: 판정 입력 fan-out payload 생성 규칙과 입력 검증을 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/nodes/rag_relevance_prepare_node.py
"""

from __future__ import annotations

import pytest

from rag_chatbot.core.chat.nodes.rag_relevance_prepare_node import rag_relevance_prepare_node
from rag_chatbot.shared.exceptions import BaseAppException


def test_rag_relevance_prepare_builds_judge_inputs() -> None:
    """후보 목록이 있으면 fan-out 판정 입력이 생성되어야 한다."""

    output = rag_relevance_prepare_node.run(
        {
            "user_message": "운영 가이드 알려줘",
            "rag_candidates": [
                {
                    "chunk_id": "c1",
                    "body": "첫 번째 본문",
                    "score": 0.2,
                },
                {
                    "chunk_id": "c2",
                    "body": "두 번째 본문",
                    "score": 0.7,
                },
            ],
        }
    )

    assert isinstance(output.get("rag_relevance_batch_id"), str)
    assert output["rag_relevance_judge_results"] == []
    assert output["rag_relevance_passed_docs"] == []

    judge_inputs = output["rag_relevance_judge_inputs"]
    assert len(judge_inputs) == 2
    assert judge_inputs[0]["rag_relevance_candidate_index"] == 0
    assert judge_inputs[1]["rag_relevance_candidate_index"] == 1
    assert judge_inputs[0]["user_query"] == "운영 가이드 알려줘"
    assert judge_inputs[0]["body"] == "첫 번째 본문"


def test_rag_relevance_prepare_raises_when_user_query_empty() -> None:
    """질문이 비어 있으면 명시적 예외가 발생해야 한다."""

    with pytest.raises(BaseAppException):
        rag_relevance_prepare_node.run(
            {
                "user_message": "",
                "rag_candidates": [],
            }
        )
