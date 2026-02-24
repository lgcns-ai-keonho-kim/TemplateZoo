"""
목적: RAG 결과 포맷 노드를 제공한다.
설명: 필터링된 문서 후보를 기반으로 rag_context와 rag_references를 생성한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/shared/chat/nodes/function_node.py, src/rag_chatbot/core/chat/prompts/chat_prompt.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypedDict, cast

from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger

_ALLOWED_REFERENCE_FIELDS = {
    "index",
    "file_name",
    "file_path",
    "page_nums",
    "score",
    "snippet",
}


class RagReferenceMetadata(TypedDict, total=False):
    """RAG reference 메타데이터 타입."""

    index: int
    file_name: str
    file_path: str
    page_nums: list[int]
    score: float
    snippet: str


class RagReference(TypedDict):
    """RAG reference 아이템 타입."""

    type: Literal["reference"]
    content: str
    metadata: RagReferenceMetadata


_rag_format_logger: Logger = create_default_logger("RagFormatNode")


def _normalize_string_list(raw_value: Any) -> list[str]:
    """문자열 목록을 trim + dedupe(순서 보존)로 정규화한다."""

    if not isinstance(raw_value, list):
        return []
    return list(
        dict.fromkeys(
            normalized
            for item in raw_value
            if (normalized := str(item or "").strip())
        )
    )


def _to_int_or_none(raw_value: Any) -> int | None:
    """값을 int로 변환하고 실패 시 None을 반환한다."""

    try:
        if isinstance(raw_value, (int, float, str)):
            return int(raw_value)
    except (TypeError, ValueError):
        return None
    return None


def _to_float_or_zero(raw_value: Any) -> float:
    """값을 float로 변환하고 실패 시 0.0을 반환한다."""

    try:
        if isinstance(raw_value, (int, float, str)):
            return float(raw_value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0


def _extract_metadata(doc: dict[str, Any]) -> dict[str, Any]:
    """문서에서 metadata dict를 안전하게 추출한다."""

    metadata = doc.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _collect_unique_metadata_values(group_docs: list[dict[str, Any]], field: str) -> list[object]:
    """그룹 문서에서 metadata[field] 값을 중복 없이 수집한다."""

    signature_to_value: dict[str, object] = {}
    for doc in group_docs:
        metadata_obj = _extract_metadata(doc)
        if field not in metadata_obj:
            continue
        value = metadata_obj[field]
        signature = repr(value)
        if signature in signature_to_value:
            continue
        signature_to_value[signature] = value
    return list(signature_to_value.values())


def _run_rag_format_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """최종 응답에 필요한 RAG 컨텍스트와 references를 생성한다."""

    raw_docs = state.get("rag_filtered_docs")
    docs = [item for item in raw_docs if isinstance(item, dict)] if isinstance(raw_docs, list) else []

    reference_fields = _normalize_string_list(state.get("rag_reference_fields"))
    metadata_fields = _normalize_string_list(state.get("rag_metadata_fields"))

    if "chunk_id" in reference_fields:
        detail = ExceptionDetail(
            code="RAG_REFERENCE_FIELDS_INVALID",
            cause="chunk_id는 references 출력에서 지원하지 않습니다.",
        )
        raise BaseAppException("reference_fields 설정이 올바르지 않습니다.", detail)

    invalid_reference_fields = [
        field
        for field in reference_fields
        if field not in _ALLOWED_REFERENCE_FIELDS
    ]
    if invalid_reference_fields:
        detail = ExceptionDetail(
            code="RAG_REFERENCE_FIELDS_INVALID",
            cause=f"허용되지 않은 reference_fields: {','.join(invalid_reference_fields)}",
        )
        raise BaseAppException("reference_fields 설정이 올바르지 않습니다.", detail)

    context_lines = [
        "[참고자료 {index}]\n- 파일명: {file_name}\n- 파일경로: {file_path}\n- 페이지: {page_num}\n- 본문:\n{body}".format(
            index=index,
            file_name=str(doc.get("file_name") or ""),
            file_path=str(doc.get("file_path") or ""),
            page_num=_extract_metadata(doc).get("page_num"),
            body=str(doc.get("body") or ""),
        )
        for index, doc in enumerate(docs, start=1)
    ]
    rag_context = "\n\n".join(context_lines)

    groups: dict[str, dict[str, Any]] = {}
    for doc in docs:
        file_name = str(doc.get("file_name") or "")
        file_path = str(doc.get("file_path") or "")
        group_key = file_path.strip() or file_name.strip() or "__empty__"
        group = groups.setdefault(
            group_key,
            {
                "file_name": file_name,
                "file_path": file_path,
                "docs": [],
            },
        )
        group["docs"].append(doc)

    references: list[RagReference] = []
    for index, group in enumerate(groups.values(), start=1):
        group_docs: list[dict[str, Any]] = group["docs"]

        seen_bodies: set[str] = set()
        merged_bodies: list[str] = []
        for doc in group_docs:
            body = str(doc.get("body") or "").strip()
            if not body:
                continue
            if body in seen_bodies:
                continue
            seen_bodies.add(body)
            merged_bodies.append(body)
        merged_body = "\n\n".join(merged_bodies)

        metadata: dict[str, Any] = {
            "index": index,
            "file_name": str(group.get("file_name") or ""),
            "file_path": str(group.get("file_path") or ""),
        }

        page_nums: list[int] = []
        seen_page_nums: set[int] = set()
        for doc in group_docs:
            page_num = _to_int_or_none(_extract_metadata(doc).get("page_num"))
            if page_num is None:
                continue
            if page_num in seen_page_nums:
                continue
            seen_page_nums.add(page_num)
            page_nums.append(page_num)
        page_nums.sort()
        if page_nums:
            metadata["page_nums"] = page_nums

        if "score" in reference_fields:
            metadata["score"] = max(
                (_to_float_or_zero(doc.get("score", 0.0)) for doc in group_docs),
                default=0.0,
            )

        if "snippet" in reference_fields:
            metadata["snippet"] = merged_body[:240]

        for field in metadata_fields:
            if field in metadata:
                continue
            values = _collect_unique_metadata_values(group_docs, field)
            if not values:
                continue
            if len(values) == 1:
                metadata[field] = values[0]
            else:
                metadata[field] = values

        references.append(
            {
                "type": "reference",
                "content": merged_body,
                "metadata": cast(RagReferenceMetadata, metadata),
            }
        )

    _rag_format_logger.info(
        "rag.format.completed: docs=%s, references=%s" % (len(docs), len(references))
    )
    return {
        "rag_context": rag_context,
        "rag_references": references,
    }


rag_format_node = function_node(
    fn=_run_rag_format_step,
    node_name="rag_format",
    logger=_rag_format_logger,
)

__all__ = ["rag_format_node", "RagReference", "RagReferenceMetadata"]
