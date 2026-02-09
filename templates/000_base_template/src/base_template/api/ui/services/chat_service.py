"""
목적: UI 조회/삭제 서비스 레이어를 제공한다.
설명: Chat API 서비스 결과를 UI 모델로 변환하고 UI 삭제 유스케이스를 수행한다.
디자인 패턴: 서비스 레이어
참조: src/base_template/api/chat/services/chat_service.py
"""

from __future__ import annotations

from typing import Optional

from base_template.api.chat.models import MessageResponse, SessionSummaryResponse
from base_template.api.chat.services import ChatAPIService, get_chat_api_service
from base_template.api.ui.models import (
    UIDeleteSessionResponse,
    UIMessageItem,
    UIMessageListResponse,
    UISessionListResponse,
    UISessionSummary,
)
from base_template.shared.logging import Logger, create_default_logger


class ChatUIService:
    """UI 조회/삭제 서비스."""

    def __init__(
        self,
        chat_service: Optional[ChatAPIService] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._logger = logger or create_default_logger("ChatUIService")
        self._chat_service = chat_service or get_chat_api_service()

    def list_sessions(self, limit: int, offset: int) -> UISessionListResponse:
        """세션 목록 조회를 처리한다."""

        response = self._chat_service.list_sessions(limit=limit, offset=offset)
        return UISessionListResponse(
            sessions=[self._to_ui_session(item) for item in response.sessions],
            limit=response.limit,
            offset=response.offset,
        )

    def list_messages(self, session_id: str, limit: int, offset: int) -> UIMessageListResponse:
        """세션 메시지 목록 조회를 처리한다."""

        response = self._chat_service.list_messages(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        return UIMessageListResponse(
            session_id=response.session_id,
            messages=[self._to_ui_message(item) for item in response.messages],
            limit=response.limit,
            offset=response.offset,
        )

    def delete_session(self, session_id: str) -> UIDeleteSessionResponse:
        """UI 세션 삭제 요청을 처리한다."""

        self._chat_service.delete_session(session_id=session_id)
        return UIDeleteSessionResponse(session_id=session_id, deleted=True)

    def _to_ui_session(self, session: SessionSummaryResponse) -> UISessionSummary:
        return UISessionSummary(
            session_id=session.session_id,
            title=session.title,
            updated_at=session.updated_at,
            message_count=session.message_count,
            last_message_preview=session.last_message_preview,
        )

    def _to_ui_message(self, message: MessageResponse) -> UIMessageItem:
        return UIMessageItem(
            message_id=message.message_id,
            role=message.role,
            content=message.content,
            sequence=message.sequence,
            created_at=message.created_at,
        )
