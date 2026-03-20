"""
목적: 로깅 모듈 공개 API를 제공한다.
설명: 로거 구현과 모델을 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_tool_calling_agent/shared/logging/logger.py, src/one_shot_tool_calling_agent/shared/logging/models.py
"""

from one_shot_tool_calling_agent.shared.logging.db_repository import DBLogRepository
from one_shot_tool_calling_agent.shared.logging.embedding_repository import (
    EmbeddingLogRepository,
)
from one_shot_tool_calling_agent.shared.logging.llm_repository import LLMLogRepository
from one_shot_tool_calling_agent.shared.logging.logger import (
    InMemoryLogger,
    LogRepository,
    Logger,
    create_default_logger,
)
from one_shot_tool_calling_agent.shared.logging.models import (
    LogContext,
    LogLevel,
    LogRecord,
)

__all__ = [
    "LogContext",
    "LogLevel",
    "LogRecord",
    "Logger",
    "LogRepository",
    "InMemoryLogger",
    "DBLogRepository",
    "LLMLogRepository",
    "EmbeddingLogRepository",
    "create_default_logger",
]
