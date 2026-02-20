"""
목적: RAG 노드 구현체를 제공한다.
설명: 사용자 질의를 기준으로 RAG 파이프라인을 실행하고 그래프 state에 컨텍스트/레퍼런스를 기록한다.
디자인 패턴: 함수형 파이프라인 위임
참조: src/rag_chatbot/shared/chat/rags/functions/pipeline.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from langchain_core.runnables.config import RunnableConfig
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.llm import LLMClient

from rag_chatbot.shared.chat.nodes._state_adapter import coerce_state_mapping
from rag_chatbot.shared.chat.rags import run_rag_pipeline
from rag_chatbot.shared.chat.rags.schemas.reference import validate_reference_field_selection
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger

_RAG_COLLECTION = "rag_chunks"


class RagNode:
    """RAG 검색 노드 구현체."""

    def __init__(
        self,
        *,
        db_client: DBClient,
        llm_client: LLMClient,
        embedder: OpenAIEmbeddings,
        collection: str = _RAG_COLLECTION,
        max_generated_keywords: int = 5,
        body_top_k: int = 5,
        relevance_filter_top_k: int = 20,
        final_top_k: int = 8,
        reference_fields: list[str] | None = None,
        metadata_fields: list[str] | None = None,
        enable_llm: bool = True,
        keyword_generation_prompt: PromptTemplate | str,
        relevance_filter_prompt: PromptTemplate | str,
        logger: Logger | None = None,
    ) -> None:
        self._logger = logger or create_default_logger("RagNode")
        self._db_client = db_client
        self._llm_client = llm_client
        self._embedder = embedder
        self._collection = collection
        self._max_generated_keywords = max(0, int(max_generated_keywords))
        self._body_top_k = max(1, int(body_top_k))
        self._relevance_filter_top_k = max(1, int(relevance_filter_top_k))
        self._final_top_k = max(1, int(final_top_k))
        normalized_reference_fields, normalized_metadata_fields = validate_reference_field_selection(
            reference_fields,
            metadata_fields,
        )
        self._reference_fields = normalized_reference_fields
        self._metadata_fields = normalized_metadata_fields
        self._enable_llm = bool(enable_llm)

        self._keyword_generation_prompt = keyword_generation_prompt
        self._relevance_filter_prompt = relevance_filter_prompt

        self._validate_prompts()

    def run(self, state: object, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
        """LangGraph 노드 진입점."""

        del config
        return self._run(coerce_state_mapping(state))

    def _run(self, state: Mapping[str, Any]) -> dict[str, Any]:
        user_query = str(state.get("user_message") or "").strip()
        if not user_query:
            detail = ExceptionDetail(
                code="RAG_QUERY_EMPTY",
                cause="user_message가 비어 있습니다.",
            )
            raise BaseAppException("RAG 검색 질의가 비어 있습니다.", detail)

        result = run_rag_pipeline(
            user_query,
            db_client=self._db_client,
            collection=self._collection,
            embed_query=self._embed_query,
            llm_client=self._llm_client,
            enable_llm=self._enable_llm,
            max_generated_keywords=self._max_generated_keywords,
            body_top_k=self._body_top_k,
            relevance_filter_top_k=self._relevance_filter_top_k,
            final_top_k=self._final_top_k,
            keyword_generation_prompt=self._keyword_generation_prompt,
            relevance_filter_prompt=self._relevance_filter_prompt,
            reference_fields=self._reference_fields,
            metadata_fields=self._metadata_fields,
            logger=self._logger,
        )

        rag_context = str(result.get("rag_context") or "")
        rag_references = result.get("rag_references")
        if not isinstance(rag_references, list):
            rag_references = []

        return {
            "rag_context": rag_context,
            "rag_references": rag_references,
        }

    def _embed_query(self, query: str) -> list[float]:
        values = self._embedder.embed_query(query)
        return [float(value) for value in values]

    def _validate_prompts(self) -> None:
        keyword_prompt_text = self._extract_prompt_text(self._keyword_generation_prompt)
        if not keyword_prompt_text:
            detail = ExceptionDetail(
                code="RAG_PROMPT_REQUIRED",
                cause="keyword_generation_prompt 누락",
            )
            raise BaseAppException("RAG 프롬프트 설정이 누락되었습니다.", detail)
        relevance_prompt_text = self._extract_prompt_text(self._relevance_filter_prompt)
        if not relevance_prompt_text:
            detail = ExceptionDetail(
                code="RAG_PROMPT_REQUIRED",
                cause="relevance_filter_prompt 누락",
            )
            raise BaseAppException("RAG 프롬프트 설정이 누락되었습니다.", detail)

    def _extract_prompt_text(self, prompt: PromptTemplate | str) -> str:
        if isinstance(prompt, PromptTemplate):
            return str(prompt.template or "").strip()
        return str(prompt or "").strip()


__all__ = ["RagNode"]
