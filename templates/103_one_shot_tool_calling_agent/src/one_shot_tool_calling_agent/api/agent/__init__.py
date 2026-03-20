"""
목적: Agent API 모듈 공개 API를 제공한다.
설명: Agent 라우터와 서비스 접근 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_tool_calling_agent/api/agent/routers/router.py, src/one_shot_tool_calling_agent/api/agent/services/runtime.py
"""

from one_shot_tool_calling_agent.api.agent.routers import router
from one_shot_tool_calling_agent.api.agent.services import (
    get_agent_service,
    shutdown_agent_api_service,
)

__all__ = ["router", "get_agent_service", "shutdown_agent_api_service"]
