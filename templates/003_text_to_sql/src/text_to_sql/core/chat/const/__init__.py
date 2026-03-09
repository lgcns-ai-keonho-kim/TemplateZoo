"""
목적: Chat 코어 상수 공개 API를 제공한다.
설명: 저장소 설정 상수와 현재 그래프 분기 상수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/core/chat/const/settings.py, src/text_to_sql/core/chat/const/routes.py
"""

from text_to_sql.core.chat.const.settings import (
    CHAT_DB_PATH,
    CHAT_MESSAGE_COLLECTION,
    CHAT_REQUEST_COMMIT_COLLECTION,
    CHAT_SESSION_COLLECTION,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from text_to_sql.core.chat.const.routes import (
    METADATA_ROUTE_RESPONSE,
    SAFEGUARD_ROUTE_BLOCKED,
    SAFEGUARD_ROUTE_RESPONSE,
)

__all__ = [
    "CHAT_DB_PATH",
    "CHAT_SESSION_COLLECTION",
    "CHAT_MESSAGE_COLLECTION",
    "CHAT_REQUEST_COMMIT_COLLECTION",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DEFAULT_CONTEXT_WINDOW",
    "SAFEGUARD_ROUTE_RESPONSE",
    "SAFEGUARD_ROUTE_BLOCKED",
    "METADATA_ROUTE_RESPONSE",
]
