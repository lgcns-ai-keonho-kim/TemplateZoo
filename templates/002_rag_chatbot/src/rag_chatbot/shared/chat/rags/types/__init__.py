"""
목적: RAG 내부 타입 공개 API를 제공한다.
설명: 검색/랭킹/reference 타입을 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/shared/chat/rags/types/*.py
"""

from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk
from rag_chatbot.shared.chat.rags.types.ranking import RelevanceFilterResult
from rag_chatbot.shared.chat.rags.types.reference import RagReference

__all__ = [
    "RetrievedChunk",
    "RelevanceFilterResult",
    "RagReference",
]
