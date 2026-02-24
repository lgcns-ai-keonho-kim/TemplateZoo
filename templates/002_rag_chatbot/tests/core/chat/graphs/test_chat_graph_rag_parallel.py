"""
목적: ChatGraph의 RAG 관련성 fan-out 라우팅 동작을 검증한다.
설명: 판정 입력 목록이 있을 때 Send 분기가 생성되는지 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.graphs.chat_graph import _route_rag_relevance_judges


def test_route_rag_relevance_judges_returns_collect_when_inputs_empty() -> None:
    """판정 입력이 없으면 collect 노드로 직접 이동해야 한다."""

    route = _route_rag_relevance_judges({"rag_relevance_judge_inputs": []})
    assert route == "rag_relevance_collect"


def test_route_rag_relevance_judges_returns_send_list() -> None:
    """판정 입력이 있으면 Send 목록을 반환해야 한다."""

    route = _route_rag_relevance_judges(
        {
            "rag_relevance_judge_inputs": [
                {
                    "rag_relevance_batch_id": "batch-1",
                    "rag_relevance_candidate_index": 0,
                    "rag_relevance_candidate": {"chunk_id": "c1"},
                    "user_query": "질문",
                    "body": "본문",
                }
            ]
        }
    )
    assert isinstance(route, list)
    assert len(route) == 1
    first = route[0]
    assert type(first).__name__ == "Send"
    node_name = getattr(first, "node", None) or getattr(first, "name", None)
    if isinstance(node_name, str):
        assert node_name == "rag_relevance_judge"
    else:
        assert "rag_relevance_judge" in repr(first)
