"""
목적: Chat API 서비스 공개 API를 제공한다.
설명: 서비스 싱글턴 접근 함수와 종료 함수를 외부에 노출한다.
디자인 패턴: 싱글턴 패턴
참조: src/base_template/api/chat/services/chat_service.py
"""

from __future__ import annotations

import threading
from typing import Optional

from base_template.api.chat.services.chat_runtime import ChatRuntime
from base_template.api.chat.services.chat_service import ChatAPIService

_chat_service: Optional[ChatAPIService] = None
_chat_service_lock = threading.RLock()


def get_chat_api_service() -> ChatAPIService:
    """Chat API 서비스 싱글턴을 반환한다."""

    global _chat_service
    if _chat_service is not None:
        return _chat_service
    with _chat_service_lock:
        if _chat_service is None:
            _chat_service = ChatAPIService()
    return _chat_service


def shutdown_chat_api_service() -> None:
    """Chat API 서비스 싱글턴을 종료한다."""

    global _chat_service
    with _chat_service_lock:
        if _chat_service is None:
            return
        _chat_service.close()
        _chat_service = None


__all__ = [
    "ChatRuntime",
    "ChatAPIService",
    "get_chat_api_service",
    "shutdown_chat_api_service",
]
