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


def _run_rag_relevance_collect_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """판정 결과를 모아 최종 통과 문서 목록을 생성한다."""

    # 1) 현재 배치 식별자를 기준으로 유효한 판정 결과만 추린다.
    #    체크포인터/재시도 환경에서는 이전 실행 결과가 state에 남을 수 있으므로
    #    batch_id를 키로 현재 실행 결과만 집계한다.
    batch_id = str(state.get("rag_relevance_batch_id") or "").strip()
    raw_results = state.get("rag_relevance_judge_results")
    matched_results = (
        [
            item
            for item in raw_results
            if isinstance(item, dict)
            and (not batch_id or str(item.get("rag_relevance_batch_id") or "") == batch_id)
        ]
        if isinstance(raw_results, list)
        else []
    )

    # 2) judge를 생략한 경로(LLM off)에서는 기존 통과 문서를 그대로 사용한다.
    #    prepare 노드에서 이미 passed_docs를 채워 준 경우를 그대로 전달해
    #    그래프 분기를 단일 collect 로직으로 흡수한다.
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
        return {
            "rag_relevance_passed_docs": passed_docs,
            "rag_relevance_judge_inputs": [],
            "rag_relevance_judge_results": [],
        }

    # 3) 원본 후보 순서를 보장하기 위해 인덱스 기준으로 정렬 후 통과 문서만 남긴다.
    #    fan-out 실행은 완료 순서가 비결정적이므로 index 정렬로 결정 순서를 복원한다.
    passed_map: dict[int, dict[str, Any]] = {}
    for item in matched_results:
        if item.get("passed") is not True:
            continue
        raw_index = item.get("rag_relevance_candidate_index")
        try:
            candidate_index = int(raw_index)
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
    return {
        "rag_relevance_passed_docs": passed_docs,
        "rag_relevance_judge_inputs": [],
        "rag_relevance_judge_results": [],
    }


rag_relevance_collect_node = function_node(
    fn=_run_rag_relevance_collect_step,
    node_name="rag_relevance_collect",
    logger=_rag_relevance_collect_logger,
)

__all__ = ["rag_relevance_collect_node"]
