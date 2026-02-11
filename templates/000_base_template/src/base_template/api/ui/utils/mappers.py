"""
목적: UI Chat 서비스 매퍼를 제공한다.
설명: Chat 도메인 엔티티를 UI DTO로 변환하는 순수 함수를 제공한다.
디자인 패턴: 매퍼 함수
참조: src/base_template/api/ui/services/chat_service.py
"""

from __future__ import annotations

from base_template.api.ui.models import UIMessageItem, UISessionSummary
from base_template.core.chat.models import ChatMessage, ChatSession


def to_ui_session(session: ChatSession) -> UISessionSummary:
    """세션 엔티티를 UI 세션 DTO로 변환한다."""

    return UISessionSummary(
        session_id=session.session_id,
        title=session.title,
        updated_at=session.updated_at,
        message_count=session.message_count,
        last_message_preview=session.last_message_preview,
    )


def to_ui_message(message: ChatMessage) -> UIMessageItem:
    """메시지 엔티티를 UI 메시지 DTO로 변환한다."""

    return UIMessageItem(
        message_id=message.message_id,
        role=message.role,
        content=message.content,
        sequence=message.sequence,
        created_at=message.created_at,
    )


__all__ = ["to_ui_message", "to_ui_session"]
