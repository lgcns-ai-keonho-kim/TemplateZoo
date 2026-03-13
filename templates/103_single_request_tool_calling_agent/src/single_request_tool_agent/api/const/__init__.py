"""
목적: API 상수 공개 API를 제공한다.
설명: Agent 라우팅 상수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/single_request_tool_agent/api/const/agent.py
"""

from single_request_tool_agent.api.const.agent import (
    AGENT_API_PREFIX,
    AGENT_API_RUN_PATH,
    AGENT_API_TAG,
)

__all__ = [
    "AGENT_API_PREFIX",
    "AGENT_API_RUN_PATH",
    "AGENT_API_TAG",
]
