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


def _to_int(value: Any, default: int | None = None) -> int | None:
    """값을 int로 변환하고 실패 시 기본값을 반환한다."""

    try:
        if isinstance(value, (int, float, str)):
            return int(value)
    except (TypeError, ValueError):
        return default
    return default


def _to_float(value: Any, default: float = 0.0) -> float:
    """값을 float로 변환하고 실패 시 기본값을 반환한다."""

    try:
        if isinstance(value, (int, float, str)):
            return float(value)
    except (TypeError, ValueError):
        return default
    return default


def _run_rag_file_page_dedup_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """관련성 통과 문서를 file/page 기준으로 중복 제거한다."""

    raw_docs = state.get("rag_relevance_passed_docs")
    passed_docs = (
        [item for item in raw_docs if isinstance(item, dict)]
        if isinstance(raw_docs, list)
        else []
    )

    # file_name + page_num 조합 기준으로 최고 점수 문서만 남긴다.
    #    page_num이 없으면 index를 페이지 번호로 대체한다.
    dedup_bucket: dict[str, dict[str, Any]] = {}
    for doc in passed_docs:
        metadata = doc.get("metadata")
        metadata_obj = metadata if isinstance(metadata, dict) else {}
        page_num = _to_int(metadata_obj.get("page_num"), None)

        if page_num is None:
            page_num = _to_int(doc.get("index"), 0)
            if page_num is None:
                page_num = 0

        key = f"{str(doc.get('file_name') or '')}::{page_num}"
        candidate_score = _to_float(doc.get("score", 0.0), 0.0)

        existing = dedup_bucket.get(key)
        if existing is None or candidate_score > _to_float(existing.get("score", 0.0), 0.0):
            dedup_bucket[key] = doc

    deduped_docs = sorted(
        dedup_bucket.values(),
        key=lambda item: _to_float(item.get("score", 0.0), 0.0),
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
