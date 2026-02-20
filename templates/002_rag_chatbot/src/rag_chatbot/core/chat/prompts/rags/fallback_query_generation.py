"""
목적: RAG fallback 질의 생성 프롬프트를 제공한다.
설명: 1차 필터 결과가 없을 때 재검색용 질의 후보를 생성한다.
디자인 패턴: 모듈 싱글턴
참조: src/rag_chatbot/shared/chat/rags/functions/fallback_query_generator.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_FALLBACK_QUERY_GENERATION_PROMPT = textwrap.dedent(
    """
    You generate fallback retrieval queries when first-pass retrieval is weak.

    Task:
    - Produce alternative search queries/keywords that increase recall without changing user intent.

    Rules:
    - Output one single line, comma-separated.
    - Output query candidates only. No explanation, numbering, quotes, JSON, or code blocks.
    - Keep candidates semantically close to the original question.
    - Include useful synonyms, abbreviations, related technical terms, and alternate phrasings.
    - Avoid overly broad generic words and remove duplicates.

    User query:
    {user_query}

    Observed context (possibly weak/noisy):
    {context}
    """
).strip()

FALLBACK_QUERY_GENERATION_PROMPT = PromptTemplate.from_template(_FALLBACK_QUERY_GENERATION_PROMPT)

__all__ = ["FALLBACK_QUERY_GENERATION_PROMPT"]
