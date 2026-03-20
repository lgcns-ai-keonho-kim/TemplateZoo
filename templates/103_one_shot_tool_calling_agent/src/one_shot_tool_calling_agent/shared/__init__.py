"""
목적: shared 패키지의 공개 API를 제공한다.
설명: 예외/로깅/런타임 유틸과 Agent 공통 모듈 접근 포인트를 제공한다.
디자인 패턴: 퍼사드
참조: src/one_shot_tool_calling_agent/shared/exceptions, src/one_shot_tool_calling_agent/shared/logging, src/one_shot_tool_calling_agent/shared/agent
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from one_shot_tool_calling_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)
from one_shot_tool_calling_agent.shared.logging import (
    DBLogRepository,
    InMemoryLogger,
    LLMLogRepository,
    LogContext,
    LogLevel,
    LogRecord,
    Logger,
    LogRepository,
    create_default_logger,
)
from one_shot_tool_calling_agent.shared.runtime import (
    InMemoryQueue,
    QueueConfig,
    QueueItem,
    RedisQueue,
    TaskRecord,
    ThreadPool,
    ThreadPoolConfig,
    Worker,
    WorkerConfig,
    WorkerState,
)

if TYPE_CHECKING:
    from one_shot_tool_calling_agent.shared.agent import (
        AgentService,
        BaseAgentGraph,
        GraphPort,
        StreamNodeConfig,
    )


_AGENT_EXPORT_NAMES = {
    "StreamNodeConfig",
    "BaseAgentGraph",
    "GraphPort",
    "AgentService",
}


def __getattr__(name: str) -> Any:
    if name in _AGENT_EXPORT_NAMES:
        from one_shot_tool_calling_agent.shared import agent as _agent

        return getattr(_agent, name)
    raise AttributeError(
        f"module 'one_shot_tool_calling_agent.shared' has no attribute '{name}'"
    )


__all__ = [
    "BaseAppException",
    "ExceptionDetail",
    "LogContext",
    "LogLevel",
    "LogRecord",
    "Logger",
    "LogRepository",
    "InMemoryLogger",
    "DBLogRepository",
    "LLMLogRepository",
    "create_default_logger",
    "StreamNodeConfig",
    "BaseAgentGraph",
    "GraphPort",
    "AgentService",
    "QueueConfig",
    "QueueItem",
    "InMemoryQueue",
    "RedisQueue",
    "WorkerConfig",
    "WorkerState",
    "Worker",
    "ThreadPoolConfig",
    "TaskRecord",
    "ThreadPool",
]
