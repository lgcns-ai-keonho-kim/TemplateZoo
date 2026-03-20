"""
목적: Chat API 모듈 공개 API를 제공한다.
설명: Chat 라우터와 서비스 접근 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/tool_proxy_agent/api/chat/routers/router.py, src/tool_proxy_agent/api/chat/services/runtime.py
"""

from tool_proxy_agent.api.chat.routers import router
from tool_proxy_agent.api.chat.services import (
    get_chat_service,
    shutdown_chat_api_service,
)

__all__ = ["router", "get_chat_service", "shutdown_chat_api_service"]
