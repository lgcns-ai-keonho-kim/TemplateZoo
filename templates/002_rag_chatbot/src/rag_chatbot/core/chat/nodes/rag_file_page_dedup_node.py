"""
목적: RAG 파일/페이지 중복 제거 노드를 제공한다.
설명: 관련성 통과 문서를 file_name + page_num(index fallback) 기준으로 중복 제거한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/core/chat/nodes/rag_relevance_collect_node.py, src/rag_chatbot/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.logging import Logger, create_default_logger

_rag_file_page_dedup_logger: Logger = create_default_logger("RagFilePageDedupNode")


def _run_rag_file_page_dedup_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """관련성 통과 문서를 file/page 기준으로 중복 제거한다."""

    # 1) 관련성 통과 문서를 안전하게 추출한다.
    #    외부/이전 단계 입력의 타입 흔들림을 방지하기 위해 dict 항목만 통과시킨다.
    raw_docs = state.get("rag_relevance_passed_docs")
    passed_docs = (
        [item for item in raw_docs if isinstance(item, dict)]
        if isinstance(raw_docs, list)
        else []
    )

    # 2) file_name + page_num 조합 기준으로 최고 점수 문서만 남긴다.
    #    page_num이 없으면 index를 페이지 번호로 대체한다.
    #    동일 페이지에서 청크가 잘게 분할된 경우가 많아 page 단위 대표 문서 1건으로 압축한다.
    dedup_bucket: dict[str, dict[str, Any]] = {}
    for doc in passed_docs:
        metadata = doc.get("metadata")
        metadata_obj = metadata if isinstance(metadata, dict) else {}
        raw_page_num = metadata_obj.get("page_num")
        page_num: int | None = None
        if isinstance(raw_page_num, (int, float, str)):
            try:
                page_num = int(raw_page_num)
            except (TypeError, ValueError):
                page_num = None

        if page_num is None:
            # 일부 인덱서는 metadata.page_num을 제공하지 않으므로 index를 fallback으로 사용한다.
            try:
                page_num = int(doc.get("index"))
            except (TypeError, ValueError):
                page_num = 0

        key = f"{str(doc.get('file_name') or '')}::{page_num}"

        score_value = doc.get("score", 0.0)
        try:
            candidate_score = float(score_value)
        except (TypeError, ValueError):
            candidate_score = 0.0

        existing = dedup_bucket.get(key)
        if existing is None:
            dedup_bucket[key] = doc
            continue

        existing_score_value = existing.get("score", 0.0)
        try:
            existing_score = float(existing_score_value)
        except (TypeError, ValueError):
            existing_score = 0.0

        if candidate_score > existing_score:
            dedup_bucket[key] = doc

    # 3) 후속 top-k 단계에서 바로 사용할 수 있게 점수 내림차순으로 정렬한다.
    #    dedup 이후에도 "더 관련성 높은 페이지 우선" 정책을 유지한다.
    deduped_docs = sorted(
        dedup_bucket.values(),
        key=lambda item: float(item.get("score", 0.0))
        if isinstance(item.get("score", 0.0), (int, float))
        else 0.0,
        reverse=True,
    )
    _rag_file_page_dedup_logger.info(
        "rag.file_page.dedup.completed: input=%s, output=%s"
        % (len(passed_docs), len(deduped_docs))
    )
    return {"rag_file_page_deduped_docs": deduped_docs}


rag_file_page_dedup_node = function_node(
    fn=_run_rag_file_page_dedup_step,
    node_name="rag_file_page_dedup",
    logger=_rag_file_page_dedup_logger,
)

__all__ = ["rag_file_page_dedup_node"]
