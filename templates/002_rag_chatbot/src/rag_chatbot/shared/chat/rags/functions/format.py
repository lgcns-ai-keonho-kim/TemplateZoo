"""
목적: RAG 컨텍스트/레퍼런스 포맷 함수를 제공한다.
설명: 응답 프롬프트 입력용 context 문자열과 UI 표시용 references를 생성한다.
디자인 패턴: 함수형 유틸
참조: src/rag_chatbot/shared/chat/rags/schemas/reference.py
"""

from __future__ import annotations

from dataclasses import dataclass

from rag_chatbot.shared.chat.rags.schemas import validate_reference_field_selection
from rag_chatbot.shared.chat.rags.types.reference import RagReference
from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk


@dataclass
class _ReferenceGroup:
    """같은 문서 기원의 검색 결과를 묶는 내부 그룹 타입."""

    file_name: str
    file_path: str
    docs: list[RetrievedChunk]


def format_rag_context(docs: list[RetrievedChunk]) -> str:
    """LLM 응답 프롬프트 입력용 context 문자열을 생성한다."""

    if not docs:
        return ""
    lines: list[str] = []
    for index, doc in enumerate(docs):
        metadata = doc.get("metadata") or {}
        page_num = metadata.get("page_num") if isinstance(metadata, dict) else None
        lines.append(
            "[참고자료 {index}]\n- 파일명: {file_name}\n- 파일경로: {file_path}\n- 페이지: {page_num}\n- 본문:\n{body}".format(
                index=index + 1,
                file_name=doc.get("file_name", ""),
                file_path=doc.get("file_path", ""),
                page_num=page_num,
                body=doc.get("body", ""),
            )
        )
    return "\n\n".join(lines)


def build_rag_references(
    docs: list[RetrievedChunk],
    *,
    reference_fields: list[str] | None,
    metadata_fields: list[str] | None,
) -> list[RagReference]:
    """UI 렌더링용 references 목록을 생성한다."""

    normalized_reference_fields, normalized_metadata_fields = validate_reference_field_selection(
        reference_fields,
        metadata_fields,
    )

    grouped_docs = _group_docs_by_document(docs)
    references: list[RagReference] = []
    for index, group in enumerate(grouped_docs, start=1):
        merged_body = _merge_group_bodies(group.docs)
        metadata = _build_reference_metadata(
            index=index,
            group=group,
            merged_body=merged_body,
            selected_reference_fields=normalized_reference_fields,
            selected_metadata_fields=normalized_metadata_fields,
        )
        item: RagReference = {
            "type": "reference",
            "content": merged_body,
            "metadata": metadata,
        }
        references.append(item)
    return references


def _group_docs_by_document(docs: list[RetrievedChunk]) -> list[_ReferenceGroup]:
    """검색 결과를 문서 단위로 그룹화한다."""

    groups: list[_ReferenceGroup] = []
    key_to_index: dict[str, int] = {}
    for doc in docs:
        file_name = str(doc.get("file_name", "") or "")
        file_path = str(doc.get("file_path", "") or "")
        key = file_path.strip() or file_name.strip()
        if not key:
            key = "__empty__"

        group_index = key_to_index.get(key)
        if group_index is None:
            key_to_index[key] = len(groups)
            groups.append(_ReferenceGroup(file_name=file_name, file_path=file_path, docs=[doc]))
            continue
        groups[group_index].docs.append(doc)
    return groups


def _merge_group_bodies(docs: list[RetrievedChunk]) -> str:
    """같은 문서 그룹의 본문을 중복 없이 결합한다."""

    bodies: list[str] = []
    seen: set[str] = set()
    for doc in docs:
        body = str(doc.get("body", "") or "").strip()
        if not body:
            continue
        if body in seen:
            continue
        seen.add(body)
        bodies.append(body)
    return "\n\n".join(bodies)


def _resolve_group_score(docs: list[RetrievedChunk]) -> float:
    """문서 그룹의 대표 score를 계산한다."""

    if not docs:
        return 0.0
    scores: list[float] = []
    for doc in docs:
        try:
            scores.append(float(doc.get("score", 0.0)))
        except (TypeError, ValueError):
            continue
    if not scores:
        return 0.0
    return max(scores)


def _build_reference_metadata(
    *,
    index: int,
    group: _ReferenceGroup,
    merged_body: str,
    selected_reference_fields: list[str],
    selected_metadata_fields: list[str],
) -> dict[str, object]:
    """reference item의 metadata를 생성한다."""

    page_nums = _collect_group_page_nums(group.docs)
    metadata: dict[str, object] = {
        "index": index,
        "file_name": group.file_name,
        "file_path": group.file_path,
    }
    if page_nums:
        metadata["page_nums"] = page_nums

    if "score" in selected_reference_fields:
        metadata["score"] = _resolve_group_score(group.docs)
    if "snippet" in selected_reference_fields:
        metadata["snippet"] = merged_body[:240]

    extra_metadata = _collect_group_metadata(group.docs, selected_metadata_fields)
    for key, value in extra_metadata.items():
        # 기본 메타데이터 키와 충돌하면 기본 값을 유지한다.
        if key in metadata:
            continue
        metadata[key] = value
    return metadata


def _collect_group_page_nums(docs: list[RetrievedChunk]) -> list[int]:
    """같은 문서 그룹의 페이지 번호 목록을 중복 없이 반환한다."""

    page_nums: list[int] = []
    seen: set[int] = set()
    for doc in docs:
        metadata = doc.get("metadata")
        if not isinstance(metadata, dict):
            continue
        raw_page_num = metadata.get("page_num")
        try:
            page_num = int(raw_page_num)
        except (TypeError, ValueError):
            continue
        if page_num in seen:
            continue
        seen.add(page_num)
        page_nums.append(page_num)
    page_nums.sort()
    return page_nums


def _collect_group_metadata(
    docs: list[RetrievedChunk],
    metadata_fields: list[str],
) -> dict[str, object]:
    """같은 문서 그룹의 메타데이터를 필드 단위로 병합한다."""

    filtered: dict[str, object] = {}
    for field in metadata_fields:
        values: list[object] = []
        seen_values: set[str] = set()
        for doc in docs:
            metadata = doc.get("metadata")
            if not isinstance(metadata, dict):
                continue
            if field not in metadata:
                continue
            value = metadata[field]
            signature = repr(value)
            if signature in seen_values:
                continue
            seen_values.add(signature)
            values.append(value)
        if not values:
            continue
        if len(values) == 1:
            filtered[field] = values[0]
            continue
        filtered[field] = values
    return filtered


__all__ = ["format_rag_context", "build_rag_references"]
