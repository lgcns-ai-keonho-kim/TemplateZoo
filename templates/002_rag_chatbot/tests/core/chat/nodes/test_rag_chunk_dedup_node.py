"""
목적: RAG 청크 dedup 노드 동작을 검증한다.
설명: chunk_id 기준으로 최고 점수 청크를 유지하는지 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/nodes/rag_chunk_dedup_node.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.nodes.rag_chunk_dedup_node import rag_chunk_dedup_node


def test_rag_chunk_dedup_keeps_highest_score() -> None:
    """동일 chunk_id에서는 최고 점수 문서만 남아야 한다."""

    output = rag_chunk_dedup_node.run(
        {
            "rag_retrieved_chunks": [
                {
                    "chunk_id": "c1",
                    "index": 1,
                    "file_name": "a.md",
                    "file_path": "/a.md",
                    "body": "body-1",
                    "metadata": {"page_num": 1},
                    "score": 0.2,
                    "source": "body",
                    "snippet": "body-1",
                },
                {
                    "chunk_id": "c1",
                    "index": 1,
                    "file_name": "a.md",
                    "file_path": "/a.md",
                    "body": "body-1-new",
                    "metadata": {"page_num": 1},
                    "score": 0.9,
                    "source": "body",
                    "snippet": "body-1-new",
                },
                {
                    "chunk_id": "c2",
                    "index": 2,
                    "file_name": "b.md",
                    "file_path": "/b.md",
                    "body": "body-2",
                    "metadata": {"page_num": 2},
                    "score": 0.5,
                    "source": "body",
                    "snippet": "body-2",
                },
            ]
        }
    )

    candidates = output["rag_candidates"]
    assert len(candidates) == 2
    assert candidates[0]["chunk_id"] == "c1"
    assert candidates[0]["score"] == 0.9
