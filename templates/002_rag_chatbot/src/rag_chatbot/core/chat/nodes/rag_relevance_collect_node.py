"""
목적: RAG 관련성 판정 집계 노드를 제공한다.
설명: fan-out 판정 결과를 배치 기준으로 모아 통과 문서를 생성한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/core/chat/nodes/rag_relevance_prepare_node.py, src/rag_chatbot/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.logging import Logger, create_default_logger

_rag_relevance_collect_logger: Logger = create_default_logger("RagRelevanceCollectNode")


def _build_collect_output(passed_docs: list[dict[str, Any]]) -> dict[str, Any]:
    """collect 노드 표준 반환 payload를 생성한다."""

    return {
        "rag_relevance_passed_docs": passed_docs,
        "rag_relevance_judge_inputs": [],
        "rag_relevance_judge_results": [],
    }


def _run_rag_relevance_collect_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """판정 결과를 모아 최종 통과 문서 목록을 생성한다."""

    batch_id = str(state.get("rag_relevance_batch_id") or "").strip()
    raw_results = state.get("rag_relevance_judge_results")
    judge_results = [item for item in raw_results if isinstance(item, dict)] if isinstance(raw_results, list) else []
    matched_results = [
        item
        for item in judge_results
        if not batch_id or str(item.get("rag_relevance_batch_id") or "") == batch_id
    ]

    # judge를 생략한 경로(_ENABLE_LLM=False)에서는 prepare가 채운 passed_docs를 그대로 사용한다.
    if not matched_results:
        raw_passed_docs = state.get("rag_relevance_passed_docs")
        passed_docs = (
            [item for item in raw_passed_docs if isinstance(item, dict)]
            if isinstance(raw_passed_docs, list)
            else []
        )
        _rag_relevance_collect_logger.info(
            "rag.relevance.collect.completed: matched=0, passed=%s" % len(passed_docs)
        )
        return _build_collect_output(passed_docs)

    # fan-out 완료 순서는 비결정적이므로 candidate_index 기준으로 순서를 복원한다.
    passed_map: dict[int, dict[str, Any]] = {}
    for item in matched_results:
        if item.get("passed") is not True:
            continue
        try:
            candidate_index = int(item.get("rag_relevance_candidate_index"))
        except (TypeError, ValueError):
            continue

        candidate = item.get("rag_relevance_candidate")
        if not isinstance(candidate, dict):
            continue
        passed_map[candidate_index] = candidate

    passed_docs = [passed_map[index] for index in sorted(passed_map.keys())]
    _rag_relevance_collect_logger.info(
        "rag.relevance.collect.completed: matched=%s, passed=%s"
        % (len(matched_results), len(passed_docs))
    )
    return _build_collect_output(passed_docs)


rag_relevance_collect_node = function_node(
    fn=_run_rag_relevance_collect_step,
    node_name="rag_relevance_collect",
    logger=_rag_relevance_collect_logger,
)

__all__ = ["rag_relevance_collect_node"]
