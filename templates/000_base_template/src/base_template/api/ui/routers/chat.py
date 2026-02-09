"""
목적: UI 조회/삭제 Chat 라우터를 제공한다.
설명: 세션 목록/메시지 이력 조회와 세션 삭제 엔드포인트를 UI(BFF) 경계로 분리한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/api/ui/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from base_template.api.ui.models import (
    UIDeleteSessionResponse,
    UIMessageListResponse,
    UISessionListResponse,
)
from base_template.api.ui.services import ChatUIService, get_chat_ui_service
from base_template.core.chat.const import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from base_template.shared.exceptions import BaseAppException

router = APIRouter(prefix="/ui-api/chat", tags=["ui-chat"])


def _to_http_exception(error: BaseAppException) -> HTTPException:
    """도메인 예외를 HTTP 예외로 변환한다."""

    code = error.detail.code
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if code in {"CHAT_SESSION_NOT_FOUND"}:
        status_code = status.HTTP_404_NOT_FOUND
    return HTTPException(status_code=status_code, detail=error.to_dict())


@router.get(
    "/sessions",
    response_model=UISessionListResponse,
    summary="UI용 대화 세션 목록을 조회합니다.",
)
def list_sessions(
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    service: ChatUIService = Depends(get_chat_ui_service),
) -> UISessionListResponse:
    """UI용 세션 목록 조회를 수행한다."""

    try:
        return service.list_sessions(limit=limit, offset=offset)
    except BaseAppException as error:
        raise _to_http_exception(error) from error


@router.get(
    "/sessions/{session_id}/messages",
    response_model=UIMessageListResponse,
    summary="UI용 세션 메시지 목록을 조회합니다.",
)
def list_messages(
    session_id: str,
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    service: ChatUIService = Depends(get_chat_ui_service),
) -> UIMessageListResponse:
    """UI용 메시지 이력 조회를 수행한다."""

    try:
        return service.list_messages(session_id=session_id, limit=limit, offset=offset)
    except BaseAppException as error:
        raise _to_http_exception(error) from error


@router.delete(
    "/sessions/{session_id}",
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
        raise _to_http_exception(error) from error
