"""
목적: 로깅 모듈 공개 API를 제공한다.
설명: 로거 구현과 모델을 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/shared/logging/logger.py, src/text_to_sql/shared/logging/models.py
"""

from text_to_sql.shared.logging.db_repository import DBLogRepository
from text_to_sql.shared.logging.embedding_repository import EmbeddingLogRepository
from text_to_sql.shared.logging.llm_repository import LLMLogRepository
from text_to_sql.shared.logging.logger import (
    InMemoryLogger,
    LogRepository,
    Logger,
    create_default_logger,
)
from text_to_sql.shared.logging.models import LogContext, LogLevel, LogRecord

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
