"""
목적: Chat 프롬프트 공개 API를 제공한다.
설명: 기본 답변 프롬프트와 안전성 분류 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/core/chat/prompts/chat_prompt.py, src/rag_chatbot/core/chat/prompts/safeguard_prompt.py
"""

from rag_chatbot.core.chat.prompts.safeguard_prompt import SAFEGUARD_PROMPT
from rag_chatbot.core.chat.prompts.chat_prompt import CHAT_PROMPT
from rag_chatbot.core.chat.prompts.fallback_query_generation import FALLBACK_QUERY_GENERATION_PROMPT
from rag_chatbot.core.chat.prompts.keyword_generation import KEYWORD_GENERATION_PROMPT
from rag_chatbot.core.chat.prompts.relevance_filter import RELEVANCE_FILTER_PROMPT

__all__ = [
    "SAFEGUARD_PROMPT",
    "CHAT_PROMPT",
    "FALLBACK_QUERY_GENERATION_PROMPT",
    "KEYWORD_GENERATION_PROMPT",
    "RELEVANCE_FILTER_PROMPT"
]
