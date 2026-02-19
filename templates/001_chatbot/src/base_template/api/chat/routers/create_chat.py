"""
목적: Chat 작업 제출 라우터를 제공한다.
설명: 사용자 입력을 JobQueue로 전달하고 request_id를 반환한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/shared/chat/services/service_executor.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from base_template.api.chat.models import SubmitChatRequest, SubmitChatResponse
from base_template.api.const import CHAT_API_CREATE_PATH
from base_template.api.chat.routers.common import to_http_exception
from base_template.api.chat.services import get_service_executor
from base_template.shared.chat import ServiceExecutor
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


@router.post(
    CHAT_API_CREATE_PATH,
    response_model=SubmitChatResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="채팅 작업을 제출합니다.",
)
def create_chat(
    request: SubmitChatRequest,
    executor: ServiceExecutor = Depends(get_service_executor),
) -> SubmitChatResponse:
    """채팅 실행 요청을 작업 큐에 적재한다."""

    try:
        queued = executor.submit_job(
            session_id=request.session_id,
            user_query=request.message,
            context_window=request.context_window,
        )
        return SubmitChatResponse(
            session_id=str(queued["session_id"]),
            request_id=str(queued["request_id"]),
            status="QUEUED",
        )
    except BaseAppException as error:
        raise to_http_exception(error) from error
