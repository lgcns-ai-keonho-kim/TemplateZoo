"""
목적: API 상수 공개 API를 제공한다.
설명: Chat/UI 라우팅 상수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/api/const/chat.py
"""

from base_template.api.const.chat import (
    CHAT_API_CREATE_PATH,
    CHAT_API_EVENTS_PATH,
    CHAT_API_PREFIX,
    CHAT_API_SESSION_SNAPSHOT_PATH,
    CHAT_API_TAG,
    UI_CHAT_API_PREFIX,
    UI_CHAT_API_TAG,
    UI_CHAT_SESSIONS_PATH,
    UI_CHAT_SESSION_MESSAGES_PATH,
    UI_CHAT_SESSION_PATH,
)

__all__ = [
    "CHAT_API_PREFIX",
    "CHAT_API_TAG",
    "CHAT_API_CREATE_PATH",
    "CHAT_API_EVENTS_PATH",
    "CHAT_API_SESSION_SNAPSHOT_PATH",
    "UI_CHAT_API_PREFIX",
    "UI_CHAT_API_TAG",
    "UI_CHAT_SESSIONS_PATH",
    "UI_CHAT_SESSION_MESSAGES_PATH",
    "UI_CHAT_SESSION_PATH",
]
