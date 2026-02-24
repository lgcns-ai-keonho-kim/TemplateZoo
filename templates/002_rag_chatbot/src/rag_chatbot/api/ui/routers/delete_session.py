"""
목적: UI Chat 세션 삭제 라우터를 제공한다.
설명: UI 세션 삭제 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/rag_chatbot/api/ui/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from rag_chatbot.api.const import UI_CHAT_SESSION_PATH
from rag_chatbot.api.ui.models import UIDeleteSessionResponse
from rag_chatbot.api.ui.routers.common import to_http_exception
from rag_chatbot.api.ui.services import ChatUIService, get_chat_ui_service
from rag_chatbot.shared.exceptions import BaseAppException

router = APIRouter()


@router.delete(
    UI_CHAT_SESSION_PATH,
    response_model=UIDeleteSessionResponse,
    summary="UI용 대화 세션과 메시지 이력을 삭제합니다.",
)
def delete_session(
    session_id: str,
    service: ChatUIService = Depends(get_chat_ui_service),
) -> UIDeleteSessionResponse:
    """UI용 세션 삭제를 수행한다."""

    try:
        return service.delete_session(session_id=session_id)
    except BaseAppException as error:
        raise to_http_exception(error) from error
