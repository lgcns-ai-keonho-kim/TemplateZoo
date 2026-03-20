"""
목적: 로거 추상 인터페이스를 제공한다.
설명: 로깅 레벨/메시지/컨텍스트 기록 계약과 컨텍스트 확장 계약을 정의한다.
디자인 패턴: 전략 패턴
참조: src/one_shot_agent/shared/logging/_in_memory_logger.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from one_shot_agent.shared.logging.models import LogContext, LogLevel


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

    def debug(self, message: str, context: Optional[LogContext] = None) -> None:
        """DEBUG 레벨 로그를 기록한다."""

        self.log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: Optional[LogContext] = None) -> None:
        """INFO 레벨 로그를 기록한다."""

        self.log(LogLevel.INFO, message, context)

    def warning(self, message: str, context: Optional[LogContext] = None) -> None:
        """WARNING 레벨 로그를 기록한다."""

        self.log(LogLevel.WARNING, message, context)

    def error(self, message: str, context: Optional[LogContext] = None) -> None:
        """ERROR 레벨 로그를 기록한다."""

        self.log(LogLevel.ERROR, message, context)

    def critical(self, message: str, context: Optional[LogContext] = None) -> None:
        """CRITICAL 레벨 로그를 기록한다."""

        self.log(LogLevel.CRITICAL, message, context)
