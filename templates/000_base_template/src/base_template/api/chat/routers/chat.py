"""
목적: Chat API 라우터를 제공한다.
설명: session_id + task_id 기반 큐/스트림/상태/결과 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/api/chat/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from base_template.api.chat.models import (
    CreateSessionRequest,
    CreateSessionResponse,
    MessageListResponse,
    QueueMessageRequest,
    QueueMessageResponse,
    TaskResultResponse,
    TaskStatusResponse,
    SessionListResponse,
)
from base_template.api.chat.services import ChatAPIService, get_chat_api_service
from base_template.core.chat.const import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from base_template.shared.exceptions import BaseAppException

router = APIRouter(prefix="/chat", tags=["chat"])


def _to_http_exception(error: BaseAppException) -> HTTPException:
    """도메인 예외를 HTTP 예외로 변환한다."""

    code = error.detail.code
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if code in {"CHAT_SESSION_NOT_FOUND"}:
        status_code = status.HTTP_404_NOT_FOUND
    if code in {"CHAT_MESSAGE_EMPTY", "CHAT_QUEUE_ERROR"}:
        status_code = status.HTTP_400_BAD_REQUEST
    if code in {"CHAT_QUEUE_FULL"}:
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    if code in {"CHAT_TASK_NOT_FOUND"}:
        status_code = status.HTTP_404_NOT_FOUND
    return HTTPException(status_code=status_code, detail=error.to_dict())


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
        raise _to_http_exception(error) from error


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="대화 세션 목록을 조회합니다.",
)
def list_sessions(
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    service: ChatAPIService = Depends(get_chat_api_service),
) -> SessionListResponse:
    """최근 대화 세션 목록을 조회한다."""

    try:
        return service.list_sessions(limit=limit, offset=offset)
    except BaseAppException as error:
        raise _to_http_exception(error) from error


@router.get(
    "/sessions/{session_id}/messages",
    response_model=MessageListResponse,
    summary="세션별 메시지 목록을 조회합니다.",
)
def list_messages(
    session_id: str,
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    service: ChatAPIService = Depends(get_chat_api_service),
) -> MessageListResponse:
    """세션 메시지를 순번 오름차순으로 조회한다."""

    try:
        return service.list_messages(session_id=session_id, limit=limit, offset=offset)
    except BaseAppException as error:
        raise _to_http_exception(error) from error


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
        raise _to_http_exception(error) from error


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
        raise _to_http_exception(error) from error


@router.get(
    "/sessions/{session_id}/tasks/{task_id}/result",
    response_model=TaskResultResponse,
    summary="세션 태스크 결과를 조회합니다.",
)
def get_task_result(
    session_id: str,
    task_id: str,
    service: ChatAPIService = Depends(get_chat_api_service),
) -> TaskResultResponse:
    """세션+태스크 기준 결과를 조회한다."""

    try:
        return service.get_task_result(session_id=session_id, task_id=task_id)
    except BaseAppException as error:
        raise _to_http_exception(error) from error


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
        raise _to_http_exception(error) from error
    return StreamingResponse(
        iterator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
