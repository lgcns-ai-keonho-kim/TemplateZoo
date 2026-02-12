"""
목적: Chat 이벤트 스트림 라우터를 제공한다.
설명: 요청 단위 EventBuffer를 소비해 SSE를 중계한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/shared/chat/services/service_executor.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from base_template.api.const import CHAT_API_EVENTS_PATH
from base_template.api.chat.routers.common import to_http_exception
from base_template.api.chat.services import get_service_executor
from base_template.shared.chat import ServiceExecutor
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


@router.get(
    CHAT_API_EVENTS_PATH,
    summary="세션 요청 단위 스트림 이벤트를 구독합니다.",
)
def stream_chat_events(
    session_id: str,
    request_id: str = Query(..., min_length=1),
    executor: ServiceExecutor = Depends(get_service_executor),
) -> StreamingResponse:
    """요청 단위 SSE 이벤트 스트림을 반환한다."""

    try:
        iterator = executor.stream_events(session_id=session_id, request_id=request_id)
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
