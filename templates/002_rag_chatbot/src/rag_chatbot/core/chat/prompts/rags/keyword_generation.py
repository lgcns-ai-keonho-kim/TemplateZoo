"""
목적: RAG 키워드 확장 프롬프트를 제공한다.
설명: 사용자 질문을 검색 확장용 comma-separated 키워드로 변환한다.
디자인 패턴: 모듈 싱글턴
참조: src/rag_chatbot/core/chat/nodes/rag_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_KEYWORD_GENERATION_PROMPT = textwrap.dedent(
    """
    You generate retrieval keywords for vector search.

    Task:
    - Produce high-signal keywords and short keyphrases from the user query.

    Rules:
    - Output one single line, comma-separated.
    - Output keywords/keyphrases only. No explanation, numbering, quotes, JSON, or code blocks.
    - Prefer concrete nouns, entities, methods, standards, and constraints.
    - Remove generic filler terms and duplicates.
    - Include Korean and/or English variants only when they improve retrieval recall.

    User query:
    {user_query}
    """
).strip()

KEYWORD_GENERATION_PROMPT = PromptTemplate.from_template(_KEYWORD_GENERATION_PROMPT)

__all__ = ["KEYWORD_GENERATION_PROMPT"]
