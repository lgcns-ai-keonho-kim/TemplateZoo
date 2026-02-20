"""
목적: RAG 프롬프트 공개 API를 제공한다.
설명: 키워드/관련성 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/core/chat/prompts/rags/*.py
"""

from rag_chatbot.core.chat.prompts.rags.keyword_generation import KEYWORD_GENERATION_PROMPT
from rag_chatbot.core.chat.prompts.rags.relevance_filter import RELEVANCE_FILTER_PROMPT

__all__ = [
    "KEYWORD_GENERATION_PROMPT",
    "RELEVANCE_FILTER_PROMPT",
]
