"""
목적: RAG reference 포맷 생성 함수를 테스트한다.
설명: 문서 단위 병합, chunk_id 비노출, metadata index 재부여 규칙을 검증한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/shared/chat/rags/functions/format.py
"""

from __future__ import annotations

from rag_chatbot.shared.chat.rags.functions.format import build_rag_references


def test_build_rag_references_merges_same_document_and_removes_chunk_id() -> None:
    """같은 문서에서 기인한 청크는 하나로 합치고 chunk_id를 제거해야 한다."""

    docs = [
        {
            "chunk_id": "c1",
            "index": 10,
            "file_name": "manual.pdf",
            "file_path": "/docs/manual.pdf",
            "body": "첫 번째 본문 단락",
            "metadata": {"page_num": 1, "section": "A"},
            "score": 0.61,
            "source": "merged",
        },
        {
            "chunk_id": "c2",
            "index": 11,
            "file_name": "manual.pdf",
            "file_path": "/docs/manual.pdf",
            "body": "두 번째 본문 단락",
            "metadata": {"page_num": 2, "section": "B"},
            "score": 0.93,
            "source": "merged",
        },
    ]

    references = build_rag_references(
        docs,
        reference_fields=["score", "snippet"],
        metadata_fields=["section"],
    )

    assert len(references) == 1
    first = references[0]
    assert first["type"] == "reference"
    assert "첫 번째 본문 단락" in first["content"]
    assert "두 번째 본문 단락" in first["content"]

    metadata = first["metadata"]
    assert metadata["index"] == 1
    assert metadata["file_name"] == "manual.pdf"
    assert metadata["file_path"] == "/docs/manual.pdf"
    assert metadata["page_nums"] == [1, 2]
    assert metadata["score"] == 0.93
    assert metadata["section"] == ["A", "B"]
    assert "chunk_id" not in metadata


def test_build_rag_references_assigns_index_in_result_order() -> None:
    """reference metadata.index는 결과 순서 기준으로 1부터 부여되어야 한다."""

    docs = [
        {
            "chunk_id": "c1",
            "index": 1,
            "file_name": "a.md",
            "file_path": "/docs/a.md",
            "body": "A 본문",
            "metadata": {"page_num": 1},
            "score": 0.8,
            "source": "merged",
        },
        {
            "chunk_id": "c2",
            "index": 2,
            "file_name": "b.md",
            "file_path": "/docs/b.md",
            "body": "B 본문",
            "metadata": {"page_num": 1},
            "score": 0.7,
            "source": "merged",
        },
    ]

    references = build_rag_references(
        docs,
        reference_fields=["score"],
        metadata_fields=None,
    )

    assert len(references) == 2
    assert references[0]["metadata"]["index"] == 1
    assert references[0]["metadata"]["file_name"] == "a.md"
    assert references[1]["metadata"]["index"] == 2
    assert references[1]["metadata"]["file_name"] == "b.md"
