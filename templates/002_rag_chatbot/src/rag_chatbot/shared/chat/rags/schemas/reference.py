"""
목적: reference 필드 선택 규칙을 제공한다.
설명: reference 기본 스키마(type/content/metadata)와 metadata 필드 선택 규칙을 검증한다.
디자인 패턴: 검증 함수
참조: src/rag_chatbot/shared/chat/rags/functions/format.py
"""

from __future__ import annotations

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_REQUIRED_REFERENCE_FIELDS = ("type", "content", "metadata")
_ALLOWED_REFERENCE_FIELDS = {
    "index",
    "file_name",
    "file_path",
    "page_nums",
    "score",
    "snippet",
}


def validate_reference_field_selection(
    reference_fields: list[str] | None,
    metadata_fields: list[str] | None,
) -> tuple[list[str], list[str]]:
    """reference 필드 선택 입력을 검증하고 정규화한다."""

    normalized_reference_fields = _normalize_list(reference_fields)
    normalized_metadata_fields = _normalize_list(metadata_fields)

    if "chunk_id" in normalized_reference_fields:
        detail = ExceptionDetail(
            code="RAG_REFERENCE_FIELDS_INVALID",
            cause="chunk_id는 references 출력에서 지원하지 않습니다.",
        )
        raise BaseAppException("reference_fields 설정이 올바르지 않습니다.", detail)

    invalid = [
        field
        for field in normalized_reference_fields
        if field not in _ALLOWED_REFERENCE_FIELDS
    ]
    if invalid:
        detail = ExceptionDetail(
            code="RAG_REFERENCE_FIELDS_INVALID",
            cause=f"허용되지 않은 reference_fields: {','.join(invalid)}",
        )
        raise BaseAppException("reference_fields 설정이 올바르지 않습니다.", detail)

    return normalized_reference_fields, normalized_metadata_fields


def build_reference_top_level_fields(reference_fields: list[str]) -> list[str]:
    """기본 스키마 필드 + 선택 필드를 합쳐 반환한다."""

    merged: list[str] = list(_REQUIRED_REFERENCE_FIELDS)
    for field in reference_fields:
        if field in merged:
            continue
        merged.append(field)
    return merged


def _normalize_list(values: list[str] | None) -> list[str]:
    if values is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        candidate = str(value or "").strip()
        if not candidate:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized


__all__ = [
    "validate_reference_field_selection",
    "build_reference_top_level_fields",
]
