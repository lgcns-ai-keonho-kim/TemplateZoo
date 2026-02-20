"""
목적: shared 패키지의 공개 API를 제공한다.
설명: 하위 공통 모듈에 대한 접근 포인트를 제공한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/shared/exceptions, src/rag_chatbot/shared/logging, src/rag_chatbot/shared/runtime
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import (
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
from rag_chatbot.shared.runtime import (
    EventBufferConfig,
    InMemoryQueue,
    InMemoryEventBuffer,
    QueueConfig,
    QueueItem,
    RedisEventBuffer,
    RedisQueue,
    StreamEventItem,
    TaskRecord,
    ThreadPool,
    ThreadPoolConfig,
    Worker,
    WorkerConfig,
    WorkerState,
)

if TYPE_CHECKING:
    from rag_chatbot.shared.chat import (
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
        from rag_chatbot.shared import chat as _chat

        return getattr(_chat, name)
    raise AttributeError(f"module 'rag_chatbot.shared' has no attribute '{name}'")


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
    "EventBufferConfig",
    "StreamEventItem",
    "InMemoryEventBuffer",
    "RedisEventBuffer",
    "WorkerConfig",
    "WorkerState",
    "Worker",
    "ThreadPoolConfig",
    "TaskRecord",
    "ThreadPool",
]
