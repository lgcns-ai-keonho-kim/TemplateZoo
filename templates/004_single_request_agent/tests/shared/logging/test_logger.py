"""
목적: 인메모리 로거와 로그 모델 동작을 검증한다.
설명: 로그 기록, 컨텍스트 병합, 저장소 공유 여부를 확인한다.
디자인 패턴: 전략 패턴, 저장소 패턴
참조: src/single_request_agent/shared/logging/logger.py, src/single_request_agent/shared/logging/models.py
"""

from __future__ import annotations

from single_request_agent.integrations.db import DBClient
from single_request_agent.integrations.db.engines.sqlite import SQLiteEngine
from single_request_agent.shared.logging import (
    DBLogRepository,
    InMemoryLogger,
    LogContext,
    LogLevel,
    LogRecord,
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


def test_db_log_repository_persists_record_with_sqlite_engine(tmp_path) -> None:
    """DB 기반 로그 저장소가 SQLite 엔진에 로그를 저장하는지 확인한다."""

    db_path = tmp_path / "logs.sqlite"
    engine = SQLiteEngine(str(db_path))
    client = DBClient(engine)
    repository = DBLogRepository(
        client=client,
        collection="logs",
        auto_create=True,
        auto_connect=True,
    )

    repository.add(
        LogRecord(
            level=LogLevel.INFO,
            message="DB 로그 저장 테스트",
            logger_name="db-log-test",
            context=LogContext(request_id="run-1"),
            metadata={"action": "invoke", "success": True},
        )
    )

    records = repository.list()
    client.close()

    assert len(records) == 1
    assert records[0].message == "DB 로그 저장 테스트"
    assert records[0].logger_name == "db-log-test"
    assert records[0].context is not None
    assert records[0].context.request_id == "run-1"
    assert records[0].metadata["action"] == "invoke"
