"""
목적: RAG 관련성 판정 준비 노드를 제공한다.
설명: 후보 문서를 검증하고 fan-out 판정 입력 목록을 생성한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/core/chat/nodes/rag_relevance_judge_node.py, src/rag_chatbot/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger

_ENABLE_LLM = True
_RELEVANCE_FILTER_TOP_K = 20
_rag_relevance_prepare_logger: Logger = create_default_logger("RagRelevancePrepareNode")


def _run_rag_relevance_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """관련성 판정 fan-out에 필요한 입력 목록을 생성한다."""

    # 1) 관련성 판정 기준 질문을 검증한다.
    user_query = str(state.get("user_message") or "").strip()
    if not user_query:
        detail = ExceptionDetail(
            code="RAG_QUERY_EMPTY",
            cause="user_message가 비어 있습니다.",
        )
        raise BaseAppException("RAG 검색 질의가 비어 있습니다.", detail)

    # 2) 후보 목록을 정규화하고 최대 개수만 유지한다.
    #    relevance 판정은 LLM 비용이 큰 단계이므로 상한(_RELEVANCE_FILTER_TOP_K)을 둔다.
    #    이 값은 "판정 품질"보다 "지연시간/비용 상한"을 보장하기 위한 운영 파라미터다.
    raw_docs = state.get("rag_candidates")
    candidates = (
        [item for item in raw_docs if isinstance(item, dict)][
            : max(1, int(_RELEVANCE_FILTER_TOP_K))
        ]
        if isinstance(raw_docs, list)
        else []
    )
    # fan-out/fan-in 과정에서 이전 실행의 잔여 결과가 섞이지 않도록 배치 식별자를 부여한다.
    batch_id = str(uuid4())

    if not candidates:
        return {
            "rag_relevance_batch_id": batch_id,
            "rag_relevance_judge_inputs": [],
            "rag_relevance_judge_results": [],
            "rag_relevance_passed_docs": [],
        }

    # 운영 상 스위치를 끈 경우 judge fan-out 없이 전체 통과로 바로 전달한다.
    # 스위치가 꺼진 경로도 출력 스키마(rag_relevance_*)를 동일하게 유지해
    # collect 노드가 분기 없이 동작하도록 맞춘다.
    if not _ENABLE_LLM:
        _rag_relevance_prepare_logger.info(
            "rag.relevance.prepare.skip_judge: input=%s, passed=%s"
            % (len(candidates), len(candidates))
        )
        return {
            "rag_relevance_batch_id": batch_id,
            "rag_relevance_judge_inputs": [],
            "rag_relevance_judge_results": [],
            "rag_relevance_passed_docs": candidates,
        }

    # 3) fan-out 각 분기에 전달할 판정 입력 payload를 생성한다.
    #    candidate_index는 collect 단계에서 원본 순서를 복원하는 기준 키다.
    #    body는 judge LLMNode에서 user_message_key로 사용된다.
    judge_inputs = [
        {
            "rag_relevance_batch_id": batch_id,
            "rag_relevance_candidate_index": candidate_index,
            "rag_relevance_candidate": candidate,
            "user_query": user_query,
            "body": str(candidate.get("body") or ""),
        }
        for candidate_index, candidate in enumerate(candidates)
    ]

    _rag_relevance_prepare_logger.info(
        "rag.relevance.prepare.completed: input=%s, fanout=%s"
        % (len(candidates), len(judge_inputs))
    )
    return {
        "rag_relevance_batch_id": batch_id,
        "rag_relevance_judge_inputs": judge_inputs,
        "rag_relevance_judge_results": [],
        "rag_relevance_passed_docs": [],
    }


rag_relevance_prepare_node = function_node(
    fn=_run_rag_relevance_prepare_step,
    node_name="rag_relevance_prepare",
    logger=_rag_relevance_prepare_logger,
)

__all__ = ["rag_relevance_prepare_node"]
