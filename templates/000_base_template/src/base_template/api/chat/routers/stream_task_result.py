"""
목적: Chat 태스크 SSE 스트림 라우터를 제공한다.
설명: 세션+태스크 기준 응답 스트림 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/api/chat/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from base_template.api.chat.routers.common import to_http_exception
from base_template.api.chat.services import ChatAPIService, get_chat_api_service
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


@router.get(
    "/sessions/{session_id}/tasks/{task_id}/stream",
    summary="세션 태스크 응답 스트림을 조회합니다.",
)
def stream_task_result(
    session_id: str,
    task_id: str,
    service: ChatAPIService = Depends(get_chat_api_service),
) -> StreamingResponse:
    """세션+태스크 기준 SSE 응답 스트림을 반환한다."""

    try:
        iterator = service.iter_task_stream_events(session_id=session_id, task_id=task_id)
    except BaseAppException as error:
        raise to_http_exception(error) from error
    return StreamingResponse(
        iterator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

