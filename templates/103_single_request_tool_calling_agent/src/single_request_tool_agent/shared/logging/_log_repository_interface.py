"""
목적: 로그 저장소 인터페이스를 제공한다.
설명: 로그 레코드 저장/조회 계약을 정의한다.
디자인 패턴: 저장소 패턴
참조: src/single_request_tool_agent/shared/logging/_in_memory_log_repository.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from single_request_tool_agent.shared.logging.models import LogRecord


class LogRepository(ABC):
    """로그 저장소 인터페이스."""

    @abstractmethod
    def add(self, record: LogRecord) -> None:
        """로그 레코드를 저장한다."""

    @abstractmethod
    def list(self) -> List[LogRecord]:
        """저장된 로그를 반환한다."""
