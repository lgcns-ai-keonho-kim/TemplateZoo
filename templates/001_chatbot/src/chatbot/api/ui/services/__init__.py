"""
목적: UI 서비스 공개 API를 제공한다.
설명: UI 조회/삭제 서비스 의존성 주입 함수를 외부에 노출한다.
디자인 패턴: 팩토리 함수
참조: src/chatbot/api/ui/services/chat_service.py
"""

from __future__ import annotations

from chatbot.api.chat.services import get_chat_service
from chatbot.api.ui.services.chat_service import ChatUIService


def get_chat_ui_service() -> ChatUIService:
    """UI 조회 서비스 인스턴스를 생성한다."""

    return ChatUIService(chat_service=get_chat_service())


__all__ = ["ChatUIService", "get_chat_ui_service"]
