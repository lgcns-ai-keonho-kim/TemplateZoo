"""
목적: 기본 로거 팩토리 함수를 제공한다.
설명: 기본 설정의 InMemoryLogger 생성 진입점을 분리한다.
디자인 패턴: 팩토리 함수
참조: src/plan_and_then_execute_agent/shared/logging/_in_memory_logger.py
"""

from __future__ import annotations

from plan_and_then_execute_agent.shared.logging._in_memory_logger import InMemoryLogger


def create_default_logger(name: str) -> InMemoryLogger:
    """기본 인메모리 로거를 생성한다."""

    return InMemoryLogger(name=name)

