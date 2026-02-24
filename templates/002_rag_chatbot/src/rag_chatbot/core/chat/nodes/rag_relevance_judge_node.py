"""
목적: RAG 청크 단건 관련성 판정 노드를 제공한다.
설명: fan-out으로 전달된 단일 후보를 LLM으로 0/1 판정하고 reducer 결과를 반환한다.
디자인 패턴: 모듈 조립 + 함수 주입 + LLMNode
참조: src/rag_chatbot/core/chat/prompts/rags/relevance_filter.py, src/rag_chatbot/shared/chat/nodes/function_node.py, src/rag_chatbot/shared/chat/nodes/llm_node.py
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from rag_chatbot.core.chat.prompts import RELEVANCE_FILTER_PROMPT
from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.chat.nodes import LLMNode
from rag_chatbot.shared.logging import Logger, create_default_logger

_rag_relevance_judge_logger: Logger = create_default_logger("RagRelevanceJudgeNode")
_BINARY_PATTERN = re.compile(r"\b([01])\b")
_rag_relevance_judge_model = ChatOpenAI(
    model_name=os.getenv("OPENAI_MODEL", ""),
    openai_api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),
    reasoning_effort="minimal",
)
_rag_relevance_judge_llm_client = LLMClient(
    model=_rag_relevance_judge_model,
    name="chat-rag-relevance-judge-llm",
)

# 단건 판정용 LLM 노드: body를 user_message로 치환해 프롬프트를 재사용한다.
# history_key를 비활성화해 청크 본문+질문만으로 판정하게 고정한다.
_rag_relevance_binary_llm_node = LLMNode(
    llm_client=_rag_relevance_judge_llm_client,
    node_name="rag_relevance_judge_llm",
    prompt=RELEVANCE_FILTER_PROMPT,
    output_key="rag_relevance_raw",
    user_message_key="body",
    history_key="__skip_history__",
    stream_tokens=False,
    logger=_rag_relevance_judge_logger,
)


async def _run_rag_relevance_judge_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """fan-out 단일 후보를 판정해 reducer 누적 결과를 반환한다."""

    batch_id = str(state.get("rag_relevance_batch_id") or "").strip()
    raw_candidate_index = state.get("rag_relevance_candidate_index")
    if isinstance(raw_candidate_index, (int, float, str)):
        try:
            candidate_index = int(raw_candidate_index)
        except (TypeError, ValueError):
            candidate_index = -1
    else:
        candidate_index = -1

    candidate = state.get("rag_relevance_candidate")
    if not isinstance(candidate, dict):
        _rag_relevance_judge_logger.warning(
            "rag.relevance.judge.skip: batch_id=%s, candidate_index=%s, cause=invalid_candidate"
            % (batch_id, candidate_index)
        )
        # reducer 초기화 신호([])를 의도치 않게 보내지 않기 위해 빈 dict를 반환한다.
        # (해당 후보만 건너뛰고 전체 배치는 계속 진행)
        return {}

    llm_state = {
        "user_query": str(state.get("user_query") or ""),
        "body": str(state.get("body") or candidate.get("body") or ""),
    }
    passed = False
    try:
        judge_output = await _rag_relevance_binary_llm_node.arun(llm_state)
        raw = str(judge_output.get("rag_relevance_raw") or "")
        text = raw.strip()
        # 프롬프트 계약은 "정확히 0 또는 1"이지만,
        # 실제 모델 출력 흔들림(공백/추가 문자열)을 고려해 완화 파싱을 적용한다.
        if text in {"0", "1"}:
            passed = text == "1"
        else:
            matched = _BINARY_PATTERN.search(text)
            if matched is not None:
                passed = matched.group(1) == "1"
            elif text[:1] in {"0", "1"}:
                passed = text.startswith("1")
    except Exception as error:  # noqa: BLE001 - 개별 후보 실패는 제외 후 계속 진행한다.
        _rag_relevance_judge_logger.warning(
            "rag.relevance.judge.error: batch_id=%s, candidate_index=%s, error=%s"
            % (batch_id, candidate_index, error)
        )
        # 실패 후보는 보수적으로 제외(불통과) 처리한다.
        passed = False

    return {
        "rag_relevance_judge_results": [
            {
                "rag_relevance_batch_id": batch_id,
                "rag_relevance_candidate_index": candidate_index,
                "rag_relevance_candidate": candidate,
                "passed": passed,
            }
        ]
    }


rag_relevance_judge_node = function_node(
    fn=_run_rag_relevance_judge_step,
    node_name="rag_relevance_judge",
    logger=_rag_relevance_judge_logger,
)

__all__ = ["rag_relevance_judge_node"]
