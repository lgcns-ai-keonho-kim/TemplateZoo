"""
목적: RAG 키워드 확장 프롬프트를 제공한다.
설명: 사용자 질문을 검색 확장용 comma-separated 키워드로 변환한다.
디자인 패턴: 모듈 싱글턴
참조: src/rag_chatbot/core/chat/nodes/rag_keyword_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_KEYWORD_GENERATION_PROMPT = textwrap.dedent(
    """
<system>
You are a retrieval specialist. Your sole task is to extract high-signal keywords and keyphrases from a user query for vector search.
</system>

<instructions>
Produce high-signal keywords and short keyphrases from the given user query.

Your response MUST adhere to the following rules without exception:
  1. Output one single line, comma-separated. No explanation, numbering, quotes, JSON, or code blocks.
  2. Prefer concrete nouns, entities, methods, standards, and constraints.
  3. Remove generic filler terms and duplicates.
  4. Include Korean and/or English variants only when they improve retrieval recall.
</instructions>

<input>
  <user_query>{user_message}</user_query>
</input>
    """
).strip()

KEYWORD_GENERATION_PROMPT = PromptTemplate.from_template(_KEYWORD_GENERATION_PROMPT)

__all__ = ["KEYWORD_GENERATION_PROMPT"]
