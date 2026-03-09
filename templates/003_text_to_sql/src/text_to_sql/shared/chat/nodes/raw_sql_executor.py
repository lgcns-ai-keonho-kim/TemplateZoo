"""
목적: 읽기 전용 raw SQL 실행기를 제공한다.
설명: 선택된 SQL target alias에 대해 단일 SELECT 문만 실행하고 결과를 dict 행 목록으로 정규화한다.
디자인 패턴: 서비스 객체
참조: src/text_to_sql/core/chat/nodes/raw_sql_execute_node.py
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from text_to_sql.integrations.db import QueryTargetRegistry
from text_to_sql.integrations.db.engines.postgres import PostgresEngine
from text_to_sql.integrations.db.engines.sqlite import SQLiteEngine
from text_to_sql.shared.logging import Logger, create_default_logger

_FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|merge|call|grant|revoke|commit|rollback|begin|vacuum|attach|detach|pragma|copy)\b",
    re.IGNORECASE,
)


class RawSQLExecutor:
    """읽기 전용 raw SQL 실행기."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger or create_default_logger("RawSQLExecutor")

    def execute(
        self,
        *,
        target_alias: str,
        sql: str,
        query_target_registry: QueryTargetRegistry | None,
    ) -> dict[str, object]:
        """단일 alias에 raw SQL을 실행한다."""

        normalized_alias = str(target_alias or "").strip()
        normalized_sql = str(sql or "").strip()
        try:
            normalized_sql = self._normalize_sql(sql)
        except ValueError as error:
            return self._failed_result(
                target_alias=normalized_alias,
                sql=normalized_sql,
                code="RAW_SQL_INVALID_FORMAT",
                message=str(error).strip() or "SQL 형식이 올바르지 않습니다.",
            )
        if query_target_registry is None:
            return self._failed_result(
                target_alias=normalized_alias,
                sql=normalized_sql,
                code="SQL_RUNTIME_NOT_INITIALIZED",
                message="query_target_registry가 초기화되지 않았습니다.",
            )

        try:
            target = query_target_registry.resolve(normalized_alias)
        except Exception as error:  # noqa: BLE001
            return self._failed_result(
                target_alias=normalized_alias,
                sql=normalized_sql,
                code="QUERY_TARGET_NOT_FOUND",
                message=f"target alias를 찾을 수 없습니다: {error}",
            )

        engine = target.client.engine
        try:
            if isinstance(engine, PostgresEngine):
                rows = self._execute_postgres(engine=engine, sql=normalized_sql)
            elif isinstance(engine, SQLiteEngine):
                rows = self._execute_sqlite(engine=engine, sql=normalized_sql)
            else:
                return self._failed_result(
                    target_alias=normalized_alias,
                    sql=normalized_sql,
                    code="RAW_SQL_ENGINE_UNSUPPORTED",
                    message="raw SQL 실행은 postgres/sqlite만 지원합니다.",
                )
        except Exception as error:  # noqa: BLE001
            if isinstance(engine, PostgresEngine):
                self._recover_postgres_connection(engine)
            self._logger.error(
                "raw.sql.execute.failed: alias=%s, sql=%s, error=%s"
                % (normalized_alias, normalized_sql, repr(error))
            )
            return self._failed_result(
                target_alias=normalized_alias,
                sql=normalized_sql,
                code="RAW_SQL_EXECUTION_FAILED",
                message=str(error).strip() or "DB 실행 오류가 발생했습니다.",
            )

        self._logger.debug(
            "raw.sql.execute: alias=%s, rows=%s, sql=%s"
            % (normalized_alias, len(rows), normalized_sql)
        )
        return {
            "target_alias": normalized_alias,
            "sql": normalized_sql,
            "status": "ok",
            "code": "RAW_SQL_OK",
            "message": "",
            "rows": rows,
            "row_count": len(rows),
        }

    def _normalize_sql(self, sql: str) -> str:
        text = str(sql or "").strip()
        while text.endswith(";"):
            text = text[:-1].rstrip()
        if not text:
            raise ValueError("SQL 문자열이 비어 있습니다.")
        if ";" in text:
            raise ValueError("단일 SQL 문만 허용됩니다.")
        lowered = text.lstrip().lower()
        if not (lowered.startswith("select") or lowered.startswith("with")):
            raise ValueError("SELECT 또는 WITH ... SELECT 문만 허용됩니다.")
        if _FORBIDDEN_SQL_PATTERN.search(text):
            raise ValueError("읽기 전용 SQL만 허용됩니다.")
        return text

    def _execute_postgres(
        self, *, engine: PostgresEngine, sql: str
    ) -> list[dict[str, object]]:
        connection = engine._connection.ensure_connection()  # noqa: SLF001
        with connection.cursor() as cursor:
            cursor.execute(sql)
            column_names = [
                str(description[0]) for description in (cursor.description or [])
            ]
            fetched = cursor.fetchall()
        connection.commit()
        return [
            {column_names[index]: value for index, value in enumerate(row)}
            for row in fetched
        ]

    def _execute_sqlite(
        self, *, engine: SQLiteEngine, sql: str
    ) -> list[dict[str, object]]:
        connection = engine._connection.ensure_connection()  # noqa: SLF001
        cursor = connection.cursor()
        rows = cursor.execute(sql).fetchall()
        normalized: list[dict[str, object]] = []
        for row in rows:
            if isinstance(row, Mapping):
                normalized.append({str(key): value for key, value in row.items()})
                continue
            try:
                normalized.append(dict(row))
            except Exception:  # noqa: BLE001
                normalized.append({})
        return normalized

    def _failed_result(
        self,
        *,
        target_alias: str,
        sql: str,
        code: str,
        message: str,
    ) -> dict[str, object]:
        return {
            "target_alias": target_alias,
            "sql": sql,
            "status": "fail",
            "code": code,
            "message": str(message or "").strip(),
            "rows": [],
            "row_count": 0,
        }

    def _recover_postgres_connection(self, engine: PostgresEngine) -> None:
        """오류가 난 PostgreSQL 연결을 rollback 또는 재연결로 복구한다."""

        try:
            connection = engine._connection.ensure_connection()  # noqa: SLF001
            connection.rollback()
            return
        except Exception as rollback_error:  # noqa: BLE001
            self._logger.warning(
                "raw.sql.rollback.failed: error=%s" % repr(rollback_error)
            )
        try:
            engine._connection.close()  # noqa: SLF001
            engine._connection.connect()  # noqa: SLF001
        except Exception as reconnect_error:  # noqa: BLE001
            self._logger.error(
                "raw.sql.reconnect.failed: error=%s" % repr(reconnect_error)
            )


__all__ = ["RawSQLExecutor"]
