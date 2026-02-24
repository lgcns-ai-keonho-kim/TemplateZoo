"""
목적: RAG 키워드 후처리 노드 동작을 검증한다.
설명: LLM 원문에서 검색 질의 목록을 생성하는 규칙을 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/nodes/rag_keyword_node.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.nodes.rag_keyword_node import rag_keyword_postprocess_node


def test_rag_keyword_postprocess_builds_queries_with_dedup() -> None:
    """원문 질의를 유지하고 키워드는 중복 없이 추가해야 한다."""

    output = rag_keyword_postprocess_node.run(
        {
            "user_message": "RAG 파이프라인",
            "rag_keyword_raw": "벡터 검색, 랭체인, 벡터 검색, 파서",
        }
    )

    assert output["rag_queries"] == [
        "RAG 파이프라인",
        "벡터 검색",
        "랭체인",
        "파서",
    ]
