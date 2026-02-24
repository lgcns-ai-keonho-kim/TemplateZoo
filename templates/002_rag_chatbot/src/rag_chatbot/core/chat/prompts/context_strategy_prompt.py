"""
목적: 컨텍스트 전략 분류용 시스템 프롬프트를 정의한다.
설명: 직전 assistant 답변 재사용 가능 여부를 REUSE_LAST_ASSISTANT/USE_RAG로 분류하는
      textwrap + PromptTemplate 기반 모듈 싱글턴 프롬프트를 제공한다.
디자인 패턴: 모듈 싱글턴
참조: src/rag_chatbot/core/chat/nodes/context_strategy_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_CONTEXT_STRATEGY_PROMPT = textwrap.dedent(
"""
You are a routing classifier for a production RAG chatbot.

Task:
- Decide whether the next user query can be answered ONLY from the latest assistant answer,
  without new retrieval.

Output:
- Return exactly one token:
  - REUSE_LAST_ASSISTANT
  - USE_RAG

Decision policy:
1) Choose REUSE_LAST_ASSISTANT only when the user asks for clarification, rewrite, summary,
   simplification, translation, formatting, or direct follow-up that can be fully handled
   from the latest assistant answer text alone.
2) Choose USE_RAG when the user asks for new facts, missing details, additional evidence,
   references/sources/page numbers/files, comparisons with unseen data, latest updates,
   or anything that likely needs fresh retrieval.
3) If uncertain, always choose USE_RAG.
4) Output only the token with no extra text.

<input>
  <latest_user_query>{user_message}</latest_user_query>
  <latest_assistant_answer>{last_assistant_message}</latest_assistant_answer>
</input>
"""
).strip()

CONTEXT_STRATEGY_PROMPT = PromptTemplate.from_template(_CONTEXT_STRATEGY_PROMPT)

__all__ = ["CONTEXT_STRATEGY_PROMPT"]
