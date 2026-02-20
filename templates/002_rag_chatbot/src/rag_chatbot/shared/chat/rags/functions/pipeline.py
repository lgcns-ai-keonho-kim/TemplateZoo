"""
목적: RAG 전체 파이프라인 함수를 제공한다.
설명: 키워드 확장, 병렬 검색, 청크별 0/1 관련성 판정, 레퍼런스 포맷을 순차 수행한다.
디자인 패턴: 파이프라인 패턴(함수형)
참조: src/rag_chatbot/core/chat/nodes/rag_node.py
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.prompts import PromptTemplate

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.rags.functions.dedup import dedup_by_file_page, merge_by_chunk_id
from rag_chatbot.shared.chat.rags.functions.binary_relevance_filter import filter_by_binary_relevance
from rag_chatbot.shared.chat.rags.functions.format import build_rag_references, format_rag_context
from rag_chatbot.shared.chat.rags.functions.query_keyword_expander import generate_query_keywords
from rag_chatbot.shared.chat.rags.functions.retrieve import search_parallel
from rag_chatbot.shared.logging import Logger


def run_rag_pipeline(
    user_query: str,
    *,
    db_client: DBClient,
    collection: str,
    embed_query: Callable[[str], list[float]],
    llm_client: LLMClient,
    enable_llm: bool,
    max_generated_keywords: int,
    body_top_k: int,
    relevance_filter_top_k: int,
    final_top_k: int,
    keyword_generation_prompt: PromptTemplate | str,
    relevance_filter_prompt: PromptTemplate | str,
    reference_fields: list[str] | None,
    metadata_fields: list[str] | None,
    logger: Logger,
) -> dict[str, Any]:
    """RAG 파이프라인을 실행한다."""

    keywords = generate_query_keywords(
        user_query,
        max_generated_keywords=max_generated_keywords,
        prompt=keyword_generation_prompt,
        llm_client=llm_client,
        enable_llm=enable_llm,
        logger=logger,
    )
    queries = [user_query] + keywords

    retrieved_docs = search_parallel(
        queries,
        db_client=db_client,
        collection=collection,
        embed_query=embed_query,
        body_top_k=body_top_k,
    )

    merged_docs = merge_by_chunk_id(retrieved_docs)
    candidate_docs = merged_docs[: max(1, relevance_filter_top_k)]
    filtered_docs = filter_by_binary_relevance(
        candidate_docs,
        user_query,
        prompt=relevance_filter_prompt,
        llm_client=llm_client,
        enable_llm=enable_llm,
        logger=logger,
    )
    final_docs = dedup_by_file_page(filtered_docs)[: max(1, final_top_k)]

    rag_context = format_rag_context(final_docs)
    rag_references = build_rag_references(
        final_docs,
        reference_fields=reference_fields,
        metadata_fields=metadata_fields,
    )

    return {
        "rag_context": rag_context,
        "rag_references": rag_references,
        "retrieved_docs": final_docs,
    }


__all__ = ["run_rag_pipeline"]
