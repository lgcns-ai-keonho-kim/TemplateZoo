"""
목적: 인메모리 로거와 로그 모델 동작을 검증한다.
설명: 로그 기록, 컨텍스트 병합, 저장소 공유 여부를 확인한다.
디자인 패턴: 전략 패턴, 저장소 패턴
참조: src/base_template/shared/logging/logger.py, src/base_template/shared/logging/models.py
"""

from __future__ import annotations

from base_template.shared.logging import (
    InMemoryLogger,
    LogContext,
    LogLevel,
    create_default_logger,
)


def test_inmemory_logger_records_log() -> None:
    """기본 로거가 로그를 기록하는지 확인한다."""

    logger = create_default_logger("unit-test")
    logger.info("시작 로그")

    records = logger.repository.list()

    assert len(records) == 1
    assert records[0].level == LogLevel.INFO
    assert records[0].message == "시작 로그"
    assert records[0].logger_name == "unit-test"


def test_logger_with_context_merges_tags() -> None:
    """컨텍스트 병합 규칙이 올바른지 확인한다."""

    base_context = LogContext(trace_id="trace-1", tags={"service": "api", "env": "dev"})
    logger = InMemoryLogger(name="ctx-test", base_context=base_context)

    logger.info("기본 컨텍스트 로그")

    child_context = LogContext(
        trace_id="trace-2",
        user_id="user-1",
        tags={"env": "prod", "feature": "search"},
    )
    child_logger = logger.with_context(child_context)
    child_logger.error("확장 컨텍스트 로그")

    records = logger.repository.list()

    assert len(records) == 2
    assert records[0].context is not None
    assert records[0].context.trace_id == "trace-1"
    assert records[0].context.tags["env"] == "dev"
    assert records[1].context is not None
    assert records[1].context.trace_id == "trace-2"
    assert records[1].context.user_id == "user-1"
    assert records[1].context.tags["env"] == "prod"
    assert records[1].context.tags["service"] == "api"
