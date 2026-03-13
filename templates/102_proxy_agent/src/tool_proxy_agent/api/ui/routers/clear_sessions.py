"""
목적: UI Chat 전체 세션 삭제 라우터를 제공한다.
설명: UI 세션 전체 삭제 엔드포인트를 정의한다.
디자인 패턴: 라우터 패턴
참조: src/tool_proxy_agent/api/ui/services/chat_service.py
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from tool_proxy_agent.api.const import UI_CHAT_SESSIONS_PATH
from tool_proxy_agent.api.ui.models import UIClearSessionsResponse
from tool_proxy_agent.api.ui.routers.common import to_http_exception
from tool_proxy_agent.api.ui.services import ChatUIService, get_chat_ui_service
from tool_proxy_agent.shared.exceptions import BaseAppException

router = APIRouter()


@router.delete(
    UI_CHAT_SESSIONS_PATH,
    response_model=UIClearSessionsResponse,
    summary="UI용 대화 세션과 메시지 이력을 모두 삭제합니다.",
)
def clear_sessions(
    service: ChatUIService = Depends(get_chat_ui_service),
) -> UIClearSessionsResponse:
    """UI용 전체 세션 삭제를 수행한다."""

    try:
        return service.clear_all_sessions()
    except BaseAppException as error:
        raise to_http_exception(error) from error
