"""
목적: RAG fallback 질의 생성 프롬프트를 제공한다.
설명: 1차 필터 결과가 없을 때 재검색용 질의 후보를 생성한다.
디자인 패턴: 모듈 싱글턴
참조: src/rag_chatbot/core/chat/nodes/rag_keyword_node.py, src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_FALLBACK_QUERY_GENERATION_PROMPT = textwrap.dedent(
    """
<system>
You are a retrieval specialist. Your sole task is to generate alternative search queries that improve recall when first-pass retrieval is weak.
</system>

<instructions>
Produce alternative search queries and keywords for the given user query and observed context.

Your response MUST adhere to the following rules without exception:
  1. Output one single line, comma-separated. No explanation, numbering, quotes, JSON, or code blocks.
  2. Keep all candidates semantically close to the original query. Do not alter user intent.
  3. Include useful synonyms, abbreviations, related technical terms, and alternate phrasings.
  4. Avoid overly broad generic terms. Remove duplicates.
</instructions>

<input>
  <user_query>{user_query}</user_query>
  <context>{context}</context>
</input>
    """
).strip()

FALLBACK_QUERY_GENERATION_PROMPT = PromptTemplate.from_template(_FALLBACK_QUERY_GENERATION_PROMPT)

__all__ = ["FALLBACK_QUERY_GENERATION_PROMPT"]
