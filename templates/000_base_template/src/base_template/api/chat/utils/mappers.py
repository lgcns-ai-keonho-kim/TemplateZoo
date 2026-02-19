"""
목적: Chat API 서비스 DTO 매퍼를 제공한다.
설명: 코어 엔티티를 API 응답 DTO로 변환하는 순수 함수를 제공한다.
디자인 패턴: 매퍼 함수
참조: src/base_template/api/chat/routers/list_sessions.py, src/base_template/api/chat/routers/list_messages.py
"""

from __future__ import annotations

from base_template.api.chat.models import MessageResponse, SessionSummaryResponse
from base_template.core.chat.models import ChatMessage, ChatSession


def to_message_response(message: ChatMessage) -> MessageResponse:
    """코어 메시지 엔티티를 API 메시지 DTO로 변환한다."""

    return MessageResponse(
        message_id=message.message_id,
        role=message.role,
        content=message.content,
        sequence=message.sequence,
        created_at=message.created_at,
    )


def to_session_summary_response(session: ChatSession) -> SessionSummaryResponse:
    """코어 세션 엔티티를 API 세션 요약 DTO로 변환한다."""

    return SessionSummaryResponse(
        session_id=session.session_id,
        title=session.title,
        updated_at=session.updated_at,
        message_count=session.message_count,
        last_message_preview=session.last_message_preview,
    )


__all__ = ["to_message_response", "to_session_summary_response"]
