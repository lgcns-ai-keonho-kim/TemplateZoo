"""
목적: RAG 관련성 필터 프롬프트를 제공한다.
설명: 단일 검색 청크가 질문과 정합한지 0/1로만 판정하도록 강제한다.
디자인 패턴: 모듈 싱글턴
참조: src/rag_chatbot/core/chat/nodes/rag_relevance_judge_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_RELEVANCE_FILTER_PROMPT = textwrap.dedent(
    """
<system>
You are a binary relevance judge. Your sole task is to decide whether a retrieval chunk can materially help answer a user query.
</system>

<instructions>
Evaluate the relevance of the chunk body against the user query.

Your response MUST adhere to the following rules without exception:
  1. Return exactly `1` for relevant or `0` for not relevant. One character only — no extra text, spaces, or newlines.
  2. Return `1` when the chunk contains direct evidence, definitions, facts, procedures, or constraints related to the query, or provides strongly related context that would improve answer quality.
  3. Return `0` when there is a topic mismatch, weak relation, or generic content with no actionable relevance, or when the chunk is empty, noisy, or unusable.
</instructions>

<input>
  <user_query>{user_query}</user_query>
  <chunk_body>{body}</chunk_body>
</input>
    """
).strip()

RELEVANCE_FILTER_PROMPT = PromptTemplate.from_template(_RELEVANCE_FILTER_PROMPT)

__all__ = ["RELEVANCE_FILTER_PROMPT"]
