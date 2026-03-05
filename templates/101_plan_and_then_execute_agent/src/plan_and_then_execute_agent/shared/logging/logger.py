"""
목적: 로깅 공개 API 파사드를 제공한다.
설명: 저장소/로거 구현의 분리 파일을 단일 진입점으로 재노출한다.
디자인 패턴: 퍼사드
참조: src/plan_and_then_execute_agent/shared/logging/_log_repository.py, src/plan_and_then_execute_agent/shared/logging/_logger_base.py, src/plan_and_then_execute_agent/shared/logging/_in_memory_logger.py
"""

from __future__ import annotations

from plan_and_then_execute_agent.shared.logging._create_default_logger import create_default_logger
from plan_and_then_execute_agent.shared.logging._in_memory_logger import InMemoryLogger
from plan_and_then_execute_agent.shared.logging._log_repository import (
    InMemoryLogRepository,
    LogRepository,
)
from plan_and_then_execute_agent.shared.logging._logger_base import Logger

__all__ = [
    "LogRepository",
    "InMemoryLogRepository",
    "Logger",
    "InMemoryLogger",
    "create_default_logger",
]
