"""
목적: UI 세션/메시지 서비스 레이어를 제공한다.
설명: Chat 도메인 서비스 결과를 UI 모델로 변환하고 생성/조회/삭제 유스케이스를 수행한다.
디자인 패턴: 서비스 레이어
참조: src/base_template/shared/chat/services/chat_service.py
"""

from __future__ import annotations

from base_template.api.ui.models import (
    UICreateSessionResponse,
    UIDeleteSessionResponse,
    UIMessageListResponse,
    UISessionListResponse,
)
from base_template.api.ui.utils.mappers import to_ui_message, to_ui_session
from base_template.shared.chat import ChatService
from base_template.shared.logging import Logger, create_default_logger


class ChatUIService:
    """UI 세션/메시지 서비스."""

    def __init__(
        self,
        chat_service: ChatService,
        logger: Logger | None = None,
    ) -> None:
        self._logger = logger or create_default_logger("ChatUIService")
        self._chat_service = chat_service

    def create_session(self, title: str | None = None) -> UICreateSessionResponse:
        """세션 생성을 처리한다."""

        session = self._chat_service.create_session(title=title)
        return UICreateSessionResponse(session_id=session.session_id)

    def list_sessions(self, limit: int, offset: int) -> UISessionListResponse:
        """세션 목록 조회를 처리한다."""

        sessions = self._chat_service.list_sessions(limit=limit, offset=offset)
        return UISessionListResponse(
            sessions=[to_ui_session(item) for item in sessions],
            limit=limit,
            offset=offset,
        )

    def list_messages(self, session_id: str, limit: int, offset: int) -> UIMessageListResponse:
        """세션 메시지 목록 조회를 처리한다."""

        messages = self._chat_service.list_messages(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        return UIMessageListResponse(
            session_id=session_id,
            messages=[to_ui_message(item) for item in messages],
            limit=limit,
            offset=offset,
        )

    def delete_session(self, session_id: str) -> UIDeleteSessionResponse:
        """UI 세션 삭제 요청을 처리한다."""

        self._chat_service.delete_session(session_id=session_id)
        return UIDeleteSessionResponse(session_id=session_id, deleted=True)
