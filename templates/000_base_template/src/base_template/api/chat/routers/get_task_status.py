"""
목적: Chat 태스크 상태 조회 라우터를 제공한다.
설명: 세션+태스크 기준 상태 조회 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/api/chat/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from base_template.api.chat.models import TaskStatusResponse
from base_template.api.chat.routers.common import to_http_exception
from base_template.api.chat.services import ChatAPIService, get_chat_api_service
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


@router.get(
    "/sessions/{session_id}/tasks/{task_id}/status",
    response_model=TaskStatusResponse,
    summary="세션 태스크 상태를 조회합니다.",
)
def get_task_status(
    session_id: str,
    task_id: str,
    service: ChatAPIService = Depends(get_chat_api_service),
) -> TaskStatusResponse:
    """세션+태스크 기준 상태를 조회한다."""

    try:
        return service.get_task_status(session_id=session_id, task_id=task_id)
    except BaseAppException as error:
        raise to_http_exception(error) from error

