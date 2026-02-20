"""
목적: RAG reference 스키마 검증 함수를 테스트한다.
설명: 필드 선택 규칙과 필수 필드 합성 규칙을 검증한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/shared/chat/rags/schemas/reference.py
"""

from __future__ import annotations

import pytest

from rag_chatbot.shared.chat.rags.schemas.reference import (
    build_reference_top_level_fields,
    validate_reference_field_selection,
)
from rag_chatbot.shared.exceptions import BaseAppException


def test_validate_reference_field_selection_rejects_chunk_id() -> None:
    """reference_fields에 chunk_id를 넣으면 예외가 발생해야 한다."""

    with pytest.raises(BaseAppException):
        validate_reference_field_selection(["chunk_id"], None)


def test_build_reference_top_level_fields_merges_required_fields() -> None:
    """필수 필드가 항상 포함되고 중복 없이 병합되는지 검증한다."""

    merged = build_reference_top_level_fields(["score", "file_path", "score"])
    assert merged == [
        "type",
        "content",
        "metadata",
        "score",
        "file_path",
    ]
