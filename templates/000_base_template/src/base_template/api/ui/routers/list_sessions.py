"""
목적: UI Chat 세션 목록 조회 라우터를 제공한다.
설명: UI 세션 목록 조회 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/base_template/api/ui/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from base_template.api.ui.models import UISessionListResponse
from base_template.api.ui.routers.common import to_http_exception
from base_template.api.ui.services import ChatUIService, get_chat_ui_service
from base_template.core.chat.const import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from base_template.shared.exceptions import BaseAppException

router = APIRouter()


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
        raise to_http_exception(error) from error

