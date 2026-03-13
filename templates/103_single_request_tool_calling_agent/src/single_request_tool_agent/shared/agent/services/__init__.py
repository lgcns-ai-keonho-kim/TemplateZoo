"""
목적: Agent 실행 서비스 공개 API를 제공한다.
설명: 1회성 Agent 실행 서비스 구현체를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/single_request_tool_agent/shared/agent/services/agent_service.py
"""

from single_request_tool_agent.shared.agent.services.agent_service import AgentService

__all__ = ["AgentService"]
