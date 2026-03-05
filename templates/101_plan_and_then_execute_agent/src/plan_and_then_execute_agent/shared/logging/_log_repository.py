"""
목적: 로그 저장소 공개 API 파사드를 제공한다.
설명: 인터페이스/인메모리 구현 분리 파일을 단일 진입점으로 재노출한다.
디자인 패턴: 퍼사드
참조: src/plan_and_then_execute_agent/shared/logging/_log_repository_interface.py, src/plan_and_then_execute_agent/shared/logging/_in_memory_log_repository.py
"""

from __future__ import annotations

from plan_and_then_execute_agent.shared.logging._in_memory_log_repository import (
    InMemoryLogRepository,
)
from plan_and_then_execute_agent.shared.logging._log_repository_interface import LogRepository

__all__ = ["LogRepository", "InMemoryLogRepository"]

