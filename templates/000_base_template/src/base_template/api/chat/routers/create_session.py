"""
목적: Chat 세션 생성 라우터를 제공한다.
설명: 신규 대화 세션 생성 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/api/chat/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from base_template.api.chat.models import CreateSessionRequest, CreateSessionResponse
from base_template.api.chat.routers.common import to_http_exception
from base_template.api.chat.services import ChatAPIService, get_chat_api_service
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


@router.post(
    "/sessions",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="대화 세션을 생성합니다.",
)
def create_session(
    request: CreateSessionRequest,
    service: ChatAPIService = Depends(get_chat_api_service),
) -> CreateSessionResponse:
    """새 대화 세션을 생성한다."""

    try:
        return service.create_session(request)
    except BaseAppException as error:
        raise to_http_exception(error) from error

