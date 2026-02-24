"""
목적: RAG 결과 포맷 노드를 제공한다.
설명: 필터링된 문서 후보를 기반으로 rag_context와 rag_references를 생성한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/shared/chat/nodes/function_node.py, src/rag_chatbot/core/chat/prompts/chat_prompt.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypedDict

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


def _run_rag_format_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """최종 응답에 필요한 RAG 컨텍스트와 references를 생성한다."""

    # 1) 최종 후보 문서와 레퍼런스 필드 설정을 안전하게 정규화한다.
    raw_docs = state.get("rag_filtered_docs")
    docs = [item for item in raw_docs if isinstance(item, dict)] if isinstance(raw_docs, list) else []

    raw_reference_fields = state.get("rag_reference_fields")
    raw_metadata_fields = state.get("rag_metadata_fields")

    # 입력 필드 목록은 공백 제거 + 중복 제거 + 순서 보존으로 정규화한다.
    # (dict.fromkeys를 사용해 첫 등장 순서를 유지)
    reference_fields = (
        list(
            dict.fromkeys(
                normalized
                for item in raw_reference_fields
                if (normalized := str(item or "").strip())
            )
        )
        if isinstance(raw_reference_fields, list)
        else []
    )

    metadata_fields = (
        list(
            dict.fromkeys(
                normalized
                for item in raw_metadata_fields
                if (normalized := str(item or "").strip())
            )
        )
        if isinstance(raw_metadata_fields, list)
        else []
    )

    # 2) 지원하지 않는 출력 필드를 사전에 차단해 런타임 혼선을 방지한다.
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

    # 3) LLM 응답 프롬프트에서 바로 소비할 수 있는 컨텍스트 텍스트를 구성한다.
    #    여기서는 "문서 순회 + 고정 포맷 텍스트"를 사용해 프롬프트 입력 형태를 안정화한다.
    context_lines = [
        "[참고자료 {index}]\n- 파일명: {file_name}\n- 파일경로: {file_path}\n- 페이지: {page_num}\n- 본문:\n{body}".format(
            index=index,
            file_name=str(doc.get("file_name") or ""),
            file_path=str(doc.get("file_path") or ""),
            page_num=(doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}).get("page_num"),
            body=str(doc.get("body") or ""),
        )
        for index, doc in enumerate(docs, start=1)
    ]
    rag_context = "\n\n".join(context_lines)

    # 4) 같은 파일 단위로 문서를 묶어 reference 집계를 위한 그룹을 만든다.
    #    file_path가 있으면 우선 사용하고, 없으면 file_name을 대체 키로 사용한다.
    #    이렇게 하면 같은 파일의 여러 페이지/청크를 하나의 reference 엔트리로 묶을 수 있다.
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

    # 5) 그룹별로 본문/페이지/점수/메타데이터를 병합해 references를 생성한다.
    #    - 본문: 중복 본문 제거 후 병합
    #    - page_nums: 정렬된 고유 페이지 목록
    #    - score: 그룹 내 최대 점수(대표 점수)
    #    - metadata_fields: 요청된 필드만 동적 병합
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

        metadata: RagReferenceMetadata = {
            "index": index,
            "file_name": str(group.get("file_name") or ""),
            "file_path": str(group.get("file_path") or ""),
        }

        page_nums: list[int] = []
        seen_page_nums: set[int] = set()
        for doc in group_docs:
            metadata_obj = doc.get("metadata")
            if not isinstance(metadata_obj, dict):
                continue
            raw_page_num = metadata_obj.get("page_num")
            try:
                page_num = int(raw_page_num)
            except (TypeError, ValueError):
                continue
            if page_num in seen_page_nums:
                continue
            seen_page_nums.add(page_num)
            page_nums.append(page_num)
        page_nums.sort()
        if page_nums:
            metadata["page_nums"] = page_nums

        if "score" in reference_fields:
            # 그룹 대표 점수는 최대값을 사용한다.
            # 평균/합산보다 "가장 강한 근거가 있는 문서"를 보존하기 유리하다.
            max_score = 0.0
            for doc in group_docs:
                raw_score = doc.get("score", 0.0)
                try:
                    score = float(raw_score)
                except (TypeError, ValueError):
                    score = 0.0
                if score > max_score:
                    max_score = score
            metadata["score"] = max_score

        if "snippet" in reference_fields:
            metadata["snippet"] = merged_body[:240]

        for field in metadata_fields:
            # metadata 값은 repr 서명을 기준으로 중복 제거한다.
            # 값 자체가 list/dict여도 안정적으로 중복 비교가 가능하도록 repr를 사용한다.
            signature_to_value: dict[str, object] = {}
            for doc in group_docs:
                metadata_obj = doc.get("metadata")
                if not isinstance(metadata_obj, dict):
                    continue
                if field not in metadata_obj:
                    continue
                value = metadata_obj[field]
                signature = repr(value)
                if signature not in signature_to_value:
                    signature_to_value[signature] = value
            values = list(signature_to_value.values())
            if not values:
                continue
            if field in metadata:
                continue
            if len(values) == 1:
                metadata[field] = values[0]
            else:
                metadata[field] = values

        references.append(
            {
                "type": "reference",
                "content": merged_body,
                "metadata": metadata,
            }
        )

    # 6) 컨텍스트/레퍼런스를 다음 응답 생성 단계 입력으로 반환한다.
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
