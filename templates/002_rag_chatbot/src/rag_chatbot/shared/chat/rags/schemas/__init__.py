"""
목적: RAG 스키마/파서 공개 API를 제공한다.
설명: 키워드/관련성/reference 파서 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/shared/chat/rags/schemas/*.py
"""

from rag_chatbot.shared.chat.rags.schemas.keyword import parse_keywords
from rag_chatbot.shared.chat.rags.schemas.binary import parse_binary_relevance
from rag_chatbot.shared.chat.rags.schemas.relevance import parse_relevance_indexes
from rag_chatbot.shared.chat.rags.schemas.reference import (
    build_reference_top_level_fields,
    validate_reference_field_selection,
)

__all__ = [
    "parse_keywords",
    "parse_binary_relevance",
    "parse_relevance_indexes",
    "validate_reference_field_selection",
    "build_reference_top_level_fields",
]
