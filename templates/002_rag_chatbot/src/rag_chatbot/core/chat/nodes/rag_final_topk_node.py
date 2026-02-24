"""
목적: RAG 최종 top-k 노드를 제공한다.
설명: file/page 중복 제거 결과를 점수 기준으로 정렬 후 최종 top-k를 반환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/core/chat/nodes/rag_file_page_dedup_node.py, src/rag_chatbot/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.logging import Logger, create_default_logger

_FINAL_TOP_K = 8
_rag_final_topk_logger: Logger = create_default_logger("RagFinalTopKNode")


def _run_rag_final_topk_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """최종 후보를 점수 기준으로 정렬해 top-k를 반환한다."""

    # 1) 파일/페이지 중복 제거 결과를 안전하게 추출한다.
    raw_docs = state.get("rag_file_page_deduped_docs")
    deduped_docs = (
        [item for item in raw_docs if isinstance(item, dict)]
        if isinstance(raw_docs, list)
        else []
    )

    # 2) 점수 내림차순 정렬 후 상위 k개만 남긴다.
    #    최종 top-k는 LLM 컨텍스트 길이/응답 지연/비용을 통제하는 마지막 안전장치다.
    #    상한을 넘는 후보는 정보량이 유사한 경우가 많아 우선순위 기반으로 절단한다.
    deduped_docs = sorted(
        deduped_docs,
        key=lambda item: float(item.get("score", 0.0))
        if isinstance(item.get("score", 0.0), (int, float))
        else 0.0,
        reverse=True,
    )
    final_docs = deduped_docs[: max(1, int(_FINAL_TOP_K))]

    _rag_final_topk_logger.info(
        "rag.final.topk.completed: input=%s, output=%s"
        % (len(deduped_docs), len(final_docs))
    )
    return {"rag_filtered_docs": final_docs}


rag_final_topk_node = function_node(
    fn=_run_rag_final_topk_step,
    node_name="rag_final_topk",
    logger=_rag_final_topk_logger,
)

__all__ = ["rag_final_topk_node"]
