"""
목적: RAG 중복 제거 함수를 테스트한다.
설명: chunk_id 및 file_name+page_num 기준 중복 제거 결과를 검증한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/shared/chat/rags/functions/dedup.py
"""

from __future__ import annotations

from rag_chatbot.shared.chat.rags.functions.dedup import dedup_by_file_page, merge_by_chunk_id


def test_merge_by_chunk_id_keeps_max_score() -> None:
    """동일 chunk_id가 여러 개일 때 최대 점수를 유지해야 한다."""

    docs = [
        {
            "chunk_id": "c1",
            "index": 1,
            "file_name": "a.md",
            "file_path": "/a.md",
            "body": "body-1",
            "metadata": {"page_num": 1},
            "score": 0.3,
            "source": "body",
        },
        {
            "chunk_id": "c1",
            "index": 1,
            "file_name": "a.md",
            "file_path": "/a.md",
            "body": "body-1",
            "metadata": {"page_num": 1},
            "score": 0.8,
            "source": "body",
        },
    ]

    merged = merge_by_chunk_id(docs)
    assert len(merged) == 1
    assert merged[0]["score"] == 0.8


def test_dedup_by_file_page_uses_page_num_or_index() -> None:
    """page_num 우선, 없으면 index로 중복 제거 키를 구성해야 한다."""

    docs = [
        {
            "chunk_id": "c1",
            "index": 1,
            "file_name": "a.md",
            "file_path": "/a.md",
            "body": "body-1",
            "metadata": {"page_num": None},
            "score": 0.4,
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

    deduped = dedup_by_file_page(docs)
    assert len(deduped) == 2
    assert deduped[0]["chunk_id"] == "c2"
    assert deduped[1]["chunk_id"] == "c3"
