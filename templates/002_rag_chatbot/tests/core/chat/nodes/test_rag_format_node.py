"""
목적: RAG 포맷 노드 동작을 검증한다.
설명: 문서 병합 결과와 reference 필드 검증 실패 케이스를 테스트한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/core/chat/nodes/rag_format_node.py
"""

from __future__ import annotations

import pytest

from rag_chatbot.core.chat.nodes.rag_format_node import rag_format_node
from rag_chatbot.shared.exceptions import BaseAppException


def test_rag_format_node_merges_same_document() -> None:
    """같은 문서 청크는 하나의 reference로 병합되어야 한다."""

    state = {
        "rag_filtered_docs": [
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
        ],
        "rag_reference_fields": ["score", "snippet"],
        "rag_metadata_fields": ["section"],
    }

    output = rag_format_node.run(state)

    references = output["rag_references"]
    assert isinstance(references, list)
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

    rag_context = output["rag_context"]
    assert isinstance(rag_context, str)
    assert "[참고자료 1]" in rag_context


def test_rag_format_node_rejects_chunk_id_reference_field() -> None:
    """reference_fields에 chunk_id가 있으면 예외가 발생해야 한다."""

    with pytest.raises(BaseAppException):
        rag_format_node.run(
            {
                "rag_filtered_docs": [],
                "rag_reference_fields": ["chunk_id"],
            }
        )
