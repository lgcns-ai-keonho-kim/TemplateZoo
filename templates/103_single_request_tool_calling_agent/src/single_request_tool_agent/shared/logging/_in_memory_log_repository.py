"""
목적: 인메모리 로그 저장소 구현체를 제공한다.
설명: 메모리 리스트 기반 로그 저장/조회 기능을 구현한다.
디자인 패턴: 저장소 패턴
참조: src/single_request_tool_agent/shared/logging/_log_repository_interface.py
"""

from __future__ import annotations

from typing import List

from single_request_tool_agent.shared.logging._log_repository_interface import (
    LogRepository,
)
from single_request_tool_agent.shared.logging.models import LogRecord


class InMemoryLogRepository(LogRepository):
    """인메모리 로그 저장소 구현체."""

    def __init__(self) -> None:
        self._records: List[LogRecord] = []

    def add(self, record: LogRecord) -> None:
        self._records.append(record)

    def list(self) -> List[LogRecord]:
        return list(self._records)
