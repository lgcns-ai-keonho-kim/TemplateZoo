"""
목적: RAG 관련성 필터 프롬프트를 제공한다.
설명: 단일 검색 청크가 질문과 정합한지 0/1로만 판정하도록 강제한다.
디자인 패턴: 모듈 싱글턴
참조: src/rag_chatbot/shared/chat/rags/functions/binary_relevance_filter.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_RELEVANCE_FILTER_PROMPT = textwrap.dedent(
    """
    You are a binary relevance judge for retrieval chunks.

    Task:
    - Decide whether the chunk body can materially help answer the user query.

    Output contract:
    - Return exactly `1` for relevant or `0` for not relevant.
    - Return one character only. No extra text, spaces, or newlines.

    Return `1` when:
    - The chunk contains direct evidence, definitions, facts, procedures, or constraints related to the query.
    - Or the chunk provides strongly related context that would improve answer quality.

    Return `0` when:
    - Topic mismatch, weak relation, or generic content with no actionable relevance.
    - Empty, noisy, or unusable text.

    User query:
    {user_query}

    Chunk body:
    {body}
    """
).strip()

RELEVANCE_FILTER_PROMPT = PromptTemplate.from_template(_RELEVANCE_FILTER_PROMPT)

__all__ = ["RELEVANCE_FILTER_PROMPT"]
