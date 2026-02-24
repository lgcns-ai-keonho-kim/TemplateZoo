"""
목적: RAG 청크 중복 제거 노드를 제공한다.
설명: 검색 원본 청크를 chunk_id 기준으로 중복 제거해 후보 목록을 생성한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py, src/rag_chatbot/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.logging import Logger, create_default_logger

_rag_chunk_dedup_logger: Logger = create_default_logger("RagChunkDedupNode")


def _run_rag_chunk_dedup_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """검색 원본 청크를 chunk_id 기준으로 중복 제거한다."""

    # 1) 상태에서 청크 목록을 안전하게 추출한다.
    #    검색 엔진 응답은 외부 입력이므로 dict 타입만 통과시켜 스키마를 안정화한다.
    raw_chunks = state.get("rag_retrieved_chunks")
    retrieved_chunks = (
        [item for item in raw_chunks if isinstance(item, dict)]
        if isinstance(raw_chunks, list)
        else []
    )

    # 2) 같은 chunk_id가 여러 번 나오면 최고 점수 문서만 유지한다.
    #    하나의 문서 청크가 여러 질의에서 동시에 매칭될 수 있으므로
    #    chunk_id를 기준으로 "대표 1건"만 남겨 중복 컨텍스트 주입을 막는다.
    dedup_bucket: dict[str, dict[str, Any]] = {}
    for chunk in retrieved_chunks:
        key = str(chunk.get("chunk_id") or "")
        if not key:
            continue

        score_value = chunk.get("score", 0.0)
        try:
            candidate_score = float(score_value)
        except (TypeError, ValueError):
            # 점수 파싱 실패 문서는 최하위 점수로 간주한다.
            candidate_score = 0.0

        existing = dedup_bucket.get(key)
        if existing is None:
            dedup_bucket[key] = chunk
            continue

        existing_score_value = existing.get("score", 0.0)
        try:
            existing_score = float(existing_score_value)
        except (TypeError, ValueError):
            existing_score = 0.0

        if candidate_score > existing_score:
            dedup_bucket[key] = chunk

    # 3) 다음 단계에서 안정적으로 처리할 수 있게 점수 내림차순으로 정렬한다.
    #    후속 relevance/filter 단계는 입력 순서가 우선순위로 작동하므로
    #    dedup 직후 정렬해 결정 순서를 고정한다.
    deduped_chunks = sorted(
        dedup_bucket.values(),
        key=lambda item: float(item.get("score", 0.0))
        if isinstance(item.get("score", 0.0), (int, float))
        else 0.0,
        reverse=True,
    )
    _rag_chunk_dedup_logger.info(
        "rag.chunk.dedup.completed: input=%s, output=%s"
        % (len(retrieved_chunks), len(deduped_chunks))
    )
    return {"rag_candidates": deduped_chunks}


rag_chunk_dedup_node = function_node(
    fn=_run_rag_chunk_dedup_step,
    node_name="rag_chunk_dedup",
    logger=_rag_chunk_dedup_logger,
)

__all__ = ["rag_chunk_dedup_node"]
