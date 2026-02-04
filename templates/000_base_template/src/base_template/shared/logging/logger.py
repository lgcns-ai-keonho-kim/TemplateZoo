"""
목적: 로거 인터페이스와 기본 구현체를 제공한다.
설명: 인메모리 저장소 기반 로거를 포함하며 저장소 주입을 지원한다.
디자인 패턴: 전략 패턴, 저장소 패턴
참조: src/base_template/shared/logging/models.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from .models import LogContext, LogLevel, LogRecord


class LogRepository(ABC):
    """로그 저장소 인터페이스."""

    @abstractmethod
    def add(self, record: LogRecord) -> None:
        """로그 레코드를 저장한다."""

    @abstractmethod
    def list(self) -> List[LogRecord]:
        """저장된 로그를 반환한다."""


class InMemoryLogRepository(LogRepository):
    """인메모리 로그 저장소 구현체."""

    def __init__(self) -> None:
        self._records: List[LogRecord] = []

    def add(self, record: LogRecord) -> None:
        self._records.append(record)

    def list(self) -> List[LogRecord]:
        return list(self._records)


class Logger(ABC):
    """로거 인터페이스."""

    @abstractmethod
    def log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """로그를 기록한다."""

    @abstractmethod
    def with_context(self, context: LogContext) -> "Logger":
        """컨텍스트가 합쳐진 새 로거를 반환한다."""


class InMemoryLogger(Logger):
    """인메모리 로거 구현체."""

    def __init__(
        self,
        name: str,
        repository: Optional[LogRepository] = None,
        base_context: Optional[LogContext] = None,
    ) -> None:
        self._name = name
        self._repository = repository or InMemoryLogRepository()
        self._base_context = base_context

    @property
    def repository(self) -> LogRepository:
        """저장소를 반환한다."""

        return self._repository

    def log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        merged_context = self._merge_context(context)
        record = LogRecord(
            level=level,
            message=message,
            timestamp=datetime.now(timezone.utc),
            logger_name=self._name,
            context=merged_context,
            metadata=metadata or {},
        )
        self._repository.add(record)

    def debug(self, message: str, context: Optional[LogContext] = None) -> None:
        self.log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: Optional[LogContext] = None) -> None:
        self.log(LogLevel.INFO, message, context)

    def warning(self, message: str, context: Optional[LogContext] = None) -> None:
        self.log(LogLevel.WARNING, message, context)

    def error(self, message: str, context: Optional[LogContext] = None) -> None:
        self.log(LogLevel.ERROR, message, context)

    def critical(self, message: str, context: Optional[LogContext] = None) -> None:
        self.log(LogLevel.CRITICAL, message, context)

    def with_context(self, context: LogContext) -> "Logger":
        merged = self._merge_context(context)
        return InMemoryLogger(
            name=self._name,
            repository=self._repository,
            base_context=merged,
        )

    def _merge_context(self, context: Optional[LogContext]) -> Optional[LogContext]:
        if self._base_context is None:
            return context
        if context is None:
            return self._base_context
        merged_tags = {**self._base_context.tags, **context.tags}
        return LogContext(
            trace_id=context.trace_id or self._base_context.trace_id,
            span_id=context.span_id or self._base_context.span_id,
            request_id=context.request_id or self._base_context.request_id,
            user_id=context.user_id or self._base_context.user_id,
            tags=merged_tags,
        )


def create_default_logger(name: str) -> InMemoryLogger:
    """기본 인메모리 로거를 생성한다."""

    return InMemoryLogger(name=name)
