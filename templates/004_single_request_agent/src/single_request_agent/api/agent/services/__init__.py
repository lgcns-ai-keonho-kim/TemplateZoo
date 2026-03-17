"""
목적: Agent API 서비스 공개 API를 제공한다.
설명: 1회성 Agent 실행 서비스와 의존성 주입 함수를 재노출한다.
디자인 패턴: 퍼사드
참조: src/single_request_agent/api/agent/services/runtime.py
"""

from single_request_agent.api.agent.services.runtime import (
    agent_service,
    get_agent_service,
    shutdown_agent_api_service,
)

__all__ = [
    "agent_service",
    "get_agent_service",
    "shutdown_agent_api_service",
]
