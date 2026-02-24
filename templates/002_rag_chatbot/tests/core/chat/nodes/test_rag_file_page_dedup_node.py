"""
목적: RAG 파일/페이지 dedup 노드 동작을 검증한다.
설명: file_name + page_num(index fallback) 기준으로 중복 제거되는지 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/nodes/rag_file_page_dedup_node.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.nodes.rag_file_page_dedup_node import rag_file_page_dedup_node


def test_rag_file_page_dedup_uses_page_num_or_index() -> None:
    """page_num 우선, 없으면 index fallback으로 dedup 키를 구성해야 한다."""

    output = rag_file_page_dedup_node.run(
        {
            "rag_relevance_passed_docs": [
                {
                    "chunk_id": "c1",
                    "index": 1,
                    "file_name": "a.md",
                    "file_path": "/a.md",
                    "body": "body-1",
                    "metadata": {"page_num": None},
                    "score": 0.2,
                    "source": "body",
                },
                {
                    "chunk_id": "c2",
                    "index": 1,
                    "file_name": "a.md",
                    "file_path": "/a.md",
                    "body": "body-2",
                    "metadata": {"page_num": None},
                    "score": 0.9,
                    "source": "body",
                },
                {
                    "chunk_id": "c3",
                    "index": 2,
                    "file_name": "a.md",
                    "file_path": "/a.md",
                    "body": "body-3",
                    "metadata": {"page_num": None},
                    "score": 0.7,
                    "source": "body",
                },
            ]
        }
    )

    deduped_docs = output["rag_file_page_deduped_docs"]
    assert len(deduped_docs) == 2
    assert deduped_docs[0]["chunk_id"] == "c2"
    assert deduped_docs[1]["chunk_id"] == "c3"
