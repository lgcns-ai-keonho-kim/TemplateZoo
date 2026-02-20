"""
목적: UI 세션 생성 라우터를 제공한다.
설명: UI 전용 세션 생성 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/rag_chatbot/api/ui/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from rag_chatbot.api.const import UI_CHAT_SESSIONS_PATH
from rag_chatbot.api.ui.models import UICreateSessionRequest, UICreateSessionResponse
from rag_chatbot.api.ui.routers.common import to_http_exception
from rag_chatbot.api.ui.services import ChatUIService, get_chat_ui_service
from rag_chatbot.shared.exceptions import BaseAppException

router = APIRouter()


@router.post(
    UI_CHAT_SESSIONS_PATH,
    response_model=UICreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="UI 세션을 생성합니다.",
)
def create_session(
    request: UICreateSessionRequest,
    service: ChatUIService = Depends(get_chat_ui_service),
) -> UICreateSessionResponse:
    """UI 세션 생성 요청을 처리한다."""

    try:
        return service.create_session(title=request.title)
    except BaseAppException as error:
        raise to_http_exception(error) from error
