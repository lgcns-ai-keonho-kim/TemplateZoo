"""
목적: RAG 관련성 collect 노드 동작을 검증한다.
설명: reducer 누적 결과를 배치 기준으로 집계해 통과 문서를 생성하는지 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/nodes/rag_relevance_collect_node.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.nodes.rag_relevance_collect_node import rag_relevance_collect_node


def test_rag_relevance_collect_sorts_passed_docs_by_index() -> None:
    """판정 완료 순서와 무관하게 후보 인덱스 순으로 통과 문서를 정렬해야 한다."""

    output = rag_relevance_collect_node.run(
        {
            "rag_relevance_batch_id": "batch-1",
            "rag_relevance_judge_results": [
                {
                    "rag_relevance_batch_id": "batch-1",
                    "rag_relevance_candidate_index": 2,
                    "rag_relevance_candidate": {"chunk_id": "c3", "body": "세 번째"},
                    "passed": True,
                },
                {
                    "rag_relevance_batch_id": "batch-1",
                    "rag_relevance_candidate_index": 0,
                    "rag_relevance_candidate": {"chunk_id": "c1", "body": "첫 번째"},
                    "passed": True,
                },
                {
                    "rag_relevance_batch_id": "batch-1",
                    "rag_relevance_candidate_index": 1,
                    "rag_relevance_candidate": {"chunk_id": "c2", "body": "두 번째"},
                    "passed": False,
                },
            ],
        }
    )

    passed_docs = output["rag_relevance_passed_docs"]
    assert [doc["chunk_id"] for doc in passed_docs] == ["c1", "c3"]
    assert output["rag_relevance_judge_inputs"] == []
    assert output["rag_relevance_judge_results"] == []


def test_rag_relevance_collect_keeps_direct_passed_docs_when_judge_skipped() -> None:
    """judge fan-out이 비어 있는 경로에서는 기존 통과 문서를 유지해야 한다."""

    output = rag_relevance_collect_node.run(
        {
            "rag_relevance_batch_id": "batch-2",
            "rag_relevance_judge_results": [
                {
                    "rag_relevance_batch_id": "stale-batch",
                    "rag_relevance_candidate_index": 0,
                    "rag_relevance_candidate": {"chunk_id": "stale"},
                    "passed": True,
                }
            ],
            "rag_relevance_passed_docs": [
                {"chunk_id": "direct-1", "body": "본문"},
            ],
        }
    )

    passed_docs = output["rag_relevance_passed_docs"]
    assert len(passed_docs) == 1
    assert passed_docs[0]["chunk_id"] == "direct-1"
