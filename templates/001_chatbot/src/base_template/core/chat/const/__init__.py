"""
목적: Chat 코어 상수 공개 API를 제공한다.
설명: 대화 저장소 경로와 컬렉션 명 상수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/chat/const/settings.py
"""

from base_template.core.chat.const.settings import (
    CHAT_DB_PATH,
    CHAT_MESSAGE_COLLECTION,
    CHAT_REQUEST_COMMIT_COLLECTION,
    CHAT_SESSION_COLLECTION,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)

__all__ = [
    "CHAT_DB_PATH",
    "CHAT_SESSION_COLLECTION",
    "CHAT_MESSAGE_COLLECTION",
    "CHAT_REQUEST_COMMIT_COLLECTION",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DEFAULT_CONTEXT_WINDOW",
]
