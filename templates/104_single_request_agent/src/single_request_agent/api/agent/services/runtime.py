"""
목적: Agent API 런타임 조립 인스턴스를 제공한다.
설명: 그래프와 1회성 실행 서비스를 모듈 레벨에서 조립해 라우터에 주입한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/single_request_agent/core/agent/graphs/chat_graph.py
"""

from __future__ import annotations

import os

from single_request_agent.core.agent.graphs import agent_graph
from single_request_agent.shared.agent import AgentService
from single_request_agent.shared.logging import Logger, create_default_logger

service_logger: Logger = create_default_logger("AgentService")
timeout_seconds = float(os.getenv("AGENT_REQUEST_TIMEOUT_SECONDS", "180.0"))

agent_service = AgentService(
    graph=agent_graph,
    timeout_seconds=timeout_seconds,
    logger=service_logger,
)


def get_agent_service() -> AgentService:
    """FastAPI Depends 경유로 AgentService 싱글턴을 반환한다."""

    return agent_service


def shutdown_agent_api_service() -> None:
    """앱 종료 시 추가 정리 작업이 없어도 동일한 종료 훅을 유지한다."""

    return None


__all__ = [
    "agent_service",
    "get_agent_service",
    "shutdown_agent_api_service",
]
