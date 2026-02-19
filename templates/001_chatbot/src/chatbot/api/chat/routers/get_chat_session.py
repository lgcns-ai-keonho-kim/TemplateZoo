"""
목적: Chat 세션 스냅샷 라우터를 제공한다.
설명: 세션 상태와 최신 메시지 목록을 한 번에 조회한다.
디자인 패턴: 라우터 패턴
참조: src/chatbot/shared/chat/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from chatbot.api.chat.models import SessionSnapshotResponse
from chatbot.api.const import CHAT_API_SESSION_SNAPSHOT_PATH
from chatbot.api.chat.routers.common import to_http_exception
from chatbot.api.chat.services import get_chat_service, get_service_executor
from chatbot.api.chat.utils.mappers import to_message_response
from chatbot.shared.chat import ChatService, ServiceExecutor
from chatbot.shared.exceptions import BaseAppException, ExceptionDetail

router = APIRouter()


@router.get(
    CHAT_API_SESSION_SNAPSHOT_PATH,
    response_model=SessionSnapshotResponse,
    summary="세션 상태/메시지 스냅샷을 조회합니다.",
)
def get_chat_session(
    session_id: str,
    service: ChatService = Depends(get_chat_service),
    executor: ServiceExecutor = Depends(get_service_executor),
) -> SessionSnapshotResponse:
    """세션 스냅샷(상태 + 메시지 목록)을 반환한다."""

    try:
        session = service.get_session(session_id=session_id)
        if session is None:
            detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={session_id}")
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        messages = service.list_messages(session_id=session_id, limit=200, offset=0)
        return SessionSnapshotResponse(
            session_id=session_id,
            messages=[to_message_response(item) for item in messages],
            last_status=executor.get_session_status(session_id=session_id) or "IDLE",
            updated_at=session.updated_at,
        )
    except BaseAppException as error:
        raise to_http_exception(error) from error
