"""
목적: RAG 키워드 생성 노드를 제공한다.
설명: LLM으로 키워드 원문을 생성하고 후처리 단계에서 검색 질의 목록을 생성한다.
디자인 패턴: 모듈 조립 + LLMNode + 함수 주입
참조: src/rag_chatbot/shared/chat/nodes/llm_node.py, src/rag_chatbot/shared/chat/nodes/function_node.py, src/rag_chatbot/core/chat/prompts/rags/keyword_generation.py
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from rag_chatbot.core.chat.prompts import KEYWORD_GENERATION_PROMPT
from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.nodes import LLMNode
from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger

_MAX_GENERATED_KEYWORDS = 3

_rag_keyword_logger: Logger = create_default_logger("RagKeywordNode")
_rag_keyword_postprocess_logger: Logger = create_default_logger("RagKeywordPostprocessNode")
_rag_keyword_model = ChatOpenAI(
    model_name=os.getenv("OPENAI_MODEL", ""),
    openai_api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),
    reasoning_effort="minimal",
)
_rag_keyword_llm_client = LLMClient(model=_rag_keyword_model, name="chat-rag-keyword-llm")


def _run_rag_keyword_postprocess_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """LLM 키워드 원문을 파싱해 검색 질의 목록을 생성한다."""

    # 1) 필수 입력 질의를 먼저 확보한다.
    #    RAG 파이프라인의 기준 질의는 반드시 user_message여야 하므로,
    #    키워드 생성 실패/빈 응답 상황에서도 원문 질의를 최소 1개 보장한다.
    user_query = str(state.get("user_message") or "").strip()
    if not user_query:
        detail = ExceptionDetail(
            code="RAG_QUERY_EMPTY",
            cause="user_message가 비어 있습니다.",
        )
        raise BaseAppException("RAG 검색 질의가 비어 있습니다.", detail)

    # 사용자 원문 질의는 항상 첫 번째에 유지한다.
    # 이렇게 하면 후속 로그/디버깅에서 "기준 질의"를 고정된 위치로 찾을 수 있다.
    queries: list[str] = [user_query]
    if _MAX_GENERATED_KEYWORDS <= 0:
        return {"rag_queries": queries}

    # 2) LLM 원문을 쉼표 단위 키워드 목록으로 정규화한다.
    #    프롬프트 계약은 comma-separated 이지만, 모델이 줄바꿈을 섞어 출력할 수 있어
    #    줄바꿈을 쉼표로 통일한 뒤 같은 파서 로직으로 처리한다.
    raw = str(state.get("rag_keyword_raw") or "")
    normalized = raw.replace("\n", ",")
    candidates = [item.strip() for item in normalized.split(",") if item.strip()]

    # 3) 중복 제거 후 최대 개수만큼 추가한다.
    #    대소문자만 다른 중복을 제거해 불필요한 임베딩/API 호출을 줄인다.
    #    상한(_MAX_GENERATED_KEYWORDS)은 검색 확장 이득과 비용(임베딩/벡터검색)을
    #    균형 맞추기 위한 운영 상 안전장치다.
    seen: set[str] = {user_query.lower()}
    generated_keywords: list[str] = []
    for candidate in candidates:
        lowered = candidate.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        generated_keywords.append(candidate)
        if len(generated_keywords) >= _MAX_GENERATED_KEYWORDS:
            break

    # 4) 사용자 원문 질의를 맨 앞에 유지한 채 최종 질의 목록을 반환한다.
    queries.extend(generated_keywords)
    _rag_keyword_postprocess_logger.info(
        "rag.keyword.generated: query_count=%s, generated=%s"
        % (len(queries), len(generated_keywords))
    )

    return {"rag_queries": queries}


rag_keyword_llm_node = LLMNode(
    llm_client=_rag_keyword_llm_client,
    node_name="rag_keyword_llm",
    prompt=KEYWORD_GENERATION_PROMPT,
    output_key="rag_keyword_raw",
    # 키워드 생성은 현재 턴 질문 중심 태스크이므로 대화 이력을 주입하지 않는다.
    # 이력을 넣으면 최근 대화 맥락이 키워드에 과도하게 섞여 검색 분산이 커질 수 있다.
    history_key="__skip_history__",
    # 본 노드는 토큰 스트리밍이 목적이 아니라 "최종 키워드 문자열 1개"가 목적이다.
    # 따라서 단건 호출(stream_tokens=False)로 단순/안정하게 유지한다.
    stream_tokens=False,
    logger=_rag_keyword_logger,
)

rag_keyword_postprocess_node = function_node(
    fn=_run_rag_keyword_postprocess_step,
    node_name="rag_keyword_postprocess",
    logger=_rag_keyword_postprocess_logger,
)

__all__ = ["rag_keyword_llm_node", "rag_keyword_postprocess_node"]
