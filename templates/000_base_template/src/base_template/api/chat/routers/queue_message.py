"""
목적: Chat 큐 등록 라우터를 제공한다.
설명: 세션 메시지를 비동기 큐에 등록하는 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/api/chat/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from base_template.api.chat.models import QueueMessageRequest, QueueMessageResponse
from base_template.api.chat.routers.common import to_http_exception
from base_template.api.chat.services import ChatAPIService, get_chat_api_service
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


@router.post(
    "/sessions/{session_id}/queue",
    response_model=QueueMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="특정 세션 메시지를 비동기 큐에 등록합니다.",
)
def queue_message(
    session_id: str,
    request: QueueMessageRequest,
    service: ChatAPIService = Depends(get_chat_api_service),
) -> QueueMessageResponse:
    """지정 세션 기준으로 태스크를 큐에 등록한다."""

    try:
        return service.enqueue_message(session_id=session_id, request=request)
    except BaseAppException as error:
        raise to_http_exception(error) from error

