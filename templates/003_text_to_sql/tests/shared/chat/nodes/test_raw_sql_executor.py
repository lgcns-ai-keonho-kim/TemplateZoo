"""
목적: raw SQL 실행기의 최소 안전 장치를 검증한다.
설명: 읽기 전용 단일 SQL 제약과 런타임 미초기화 실패를 명시적으로 반환하는지 확인한다.
디자인 패턴: 서비스 단위 테스트
참조: src/text_to_sql/shared/chat/nodes/raw_sql_executor.py
"""

from __future__ import annotations

import pytest

from text_to_sql.shared.chat.nodes.raw_sql_executor import RawSQLExecutor


def test_raw_sql_executor_rejects_multi_statement_sql() -> None:
    """세미콜론으로 구분된 다중 문은 허용되지 않아야 한다."""

    executor = RawSQLExecutor()

    with pytest.raises(ValueError):
        executor._normalize_sql("SELECT 1; SELECT 2")


def test_raw_sql_executor_rejects_non_select_sql() -> None:
    """쓰기 SQL은 읽기 전용 가드에서 차단되어야 한다."""

    executor = RawSQLExecutor()

    with pytest.raises(ValueError):
        executor._normalize_sql("DELETE FROM data.AGENTS")


def test_raw_sql_executor_returns_explicit_runtime_error_without_registry() -> None:
    """런타임 registry가 없으면 명시적 실패 결과를 반환해야 한다."""

    executor = RawSQLExecutor()
    result = executor.execute(
        target_alias="ecommerce",
        sql="SELECT 1",
        query_target_registry=None,
    )

    assert result["status"] == "fail"
    assert result["code"] == "SQL_RUNTIME_NOT_INITIALIZED"


def test_raw_sql_executor_returns_failure_result_for_invalid_sql_format() -> None:
    """잘못된 SQL 형식은 예외 대신 명시적 실패 결과로 정규화해야 한다."""

    executor = RawSQLExecutor()
    result = executor.execute(
        target_alias="ecommerce",
        sql="[{'type': 'text', 'text': 'SELECT 1'}]",
        query_target_registry=None,
    )

    assert result["status"] == "fail"
    assert result["code"] == "RAW_SQL_INVALID_FORMAT"
