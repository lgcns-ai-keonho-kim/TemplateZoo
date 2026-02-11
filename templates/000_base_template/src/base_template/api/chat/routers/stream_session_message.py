"""
목적: Chat 단일 스트림 라우터를 제공한다.
설명: 세션 메시지 입력과 스트리밍 응답을 하나의 엔드포인트로 처리한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/shared/chat/services/service_executor.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from base_template.api.chat.models import StreamMessageRequest
from base_template.api.chat.routers.common import to_http_exception
from base_template.api.chat.services import get_service_executor
from base_template.shared.chat import ServiceExecutor
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


@router.post(
    "/sessions/{session_id}/messages/stream",
    summary="세션 메시지를 전송하고 스트리밍 응답을 수신합니다.",
)
def stream_session_message(
    session_id: str,
    request: StreamMessageRequest,
    executor: ServiceExecutor = Depends(get_service_executor),
) -> StreamingResponse:
    """세션 단일 스트림 실행을 시작한다."""

    try:
        iterator = executor.run_stream(
            session_id=session_id,
            user_query=request.message,
            context_window=request.context_window,
        )
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
