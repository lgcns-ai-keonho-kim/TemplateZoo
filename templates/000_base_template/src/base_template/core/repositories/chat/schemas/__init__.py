"""
목적: Chat 스키마 모듈 공개 API를 제공한다.
설명: 세션/메시지 스키마 생성 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/repositories/chat/schemas/session_schema.py
"""

from base_template.core.repositories.chat.schemas.message_schema import build_chat_message_schema
from base_template.core.repositories.chat.schemas.session_schema import build_chat_session_schema

__all__ = [
    "build_chat_session_schema",
    "build_chat_message_schema",
]
