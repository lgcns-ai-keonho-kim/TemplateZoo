"""
목적: shared 패키지의 공개 API를 제공한다.
설명: 하위 공통 모듈에 대한 접근 포인트를 제공한다.
디자인 패턴: 퍼사드
참조: src/base_template/shared/exceptions, src/base_template/shared/logging, src/base_template/shared/runtime
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import (
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
from base_template.shared.runtime import (
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
    from base_template.shared.chat import (
        BaseChatGraph,
        ChatHistoryRepository,
        ChatService,
        ChatServicePort,
        ChatSessionMemoryStore,
        GraphPort,
        ServiceExecutor,
        ServiceExecutorPort,
        StreamNodeConfig,
    )


_CHAT_EXPORT_NAMES = {
    "StreamNodeConfig",
    "BaseChatGraph",
    "GraphPort",
    "ChatServicePort",
    "ServiceExecutorPort",
    "ChatService",
    "ServiceExecutor",
    "ChatSessionMemoryStore",
    "ChatHistoryRepository",
}


def __getattr__(name: str) -> Any:
    if name in _CHAT_EXPORT_NAMES:
        from base_template.shared import chat as _chat

        return getattr(_chat, name)
    raise AttributeError(f"module 'base_template.shared' has no attribute '{name}'")


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
    "BaseChatGraph",
    "GraphPort",
    "ChatServicePort",
    "ServiceExecutorPort",
    "ChatService",
    "ServiceExecutor",
    "ChatSessionMemoryStore",
    "ChatHistoryRepository",
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
