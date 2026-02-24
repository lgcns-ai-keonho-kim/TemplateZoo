"""
목적: SQLite 스키마 관리 모듈을 제공한다.
설명: 컬렉션 생성/삭제와 컬럼 추가/삭제를 담당한다.
디자인 패턴: 매니저 패턴
참조: src/rag_chatbot/integrations/db/engines/sqlite/engine.py
"""

from __future__ import annotations

import sqlite3
from typing import Callable

from rag_chatbot.integrations.db.base.models import CollectionSchema, ColumnSpec
from rag_chatbot.integrations.db.engines.sql_common import SQLIdentifierHelper


class SqliteSchemaManager:
    """SQLite 스키마 관리자."""

    def __init__(
        self,
        connection_provider: Callable[[], sqlite3.Connection],
        identifier_helper: SQLIdentifierHelper,
    ) -> None:
        self._connection_provider = connection_provider
        self._identifier = identifier_helper

    def create_collection(self, schema: CollectionSchema) -> None:
        """스키마 기반 테이블을 생성한다."""

        self._ensure_no_vector_schema(schema)
        connection = self._connection_provider()
        table = self._identifier.quote_table(schema.name)
        cursor = connection.cursor()
        if schema.columns:
            column_defs = []
            for column in schema.columns:
                col_name = self._identifier.quote_identifier(column.name)
                data_type = self._resolve_column_type(schema, column)
                col_def = f"{col_name} {data_type}"
                if not column.nullable:
                    col_def += " NOT NULL"
                if column.is_primary or column.name == schema.primary_key:
                    col_def += " PRIMARY KEY"
                column_defs.append(col_def)
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
            )
        else:
            column_defs = [f"{self._identifier.quote_identifier(schema.primary_key)} TEXT PRIMARY KEY"]
            if schema.payload_field:
                column_defs.append(
                    f"{self._identifier.quote_identifier(schema.payload_field)} TEXT"
                )
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
            )

    def delete_collection(self, name: str) -> None:
        """컬렉션을 삭제한다."""

        connection = self._connection_provider()
        table = self._identifier.quote_table(name)
        cursor = connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    def add_column(self, schema: CollectionSchema, column: ColumnSpec) -> None:
        """컬럼을 추가한다."""

        if column.is_primary or column.name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 추가할 수 없습니다.")
        if column.is_vector or column.name == schema.vector_field:
            raise RuntimeError("SQLite 엔진은 벡터 컬럼을 지원하지 않습니다.")
        connection = self._connection_provider()
        table = self._identifier.quote_table(schema.name)
        column_name = self._identifier.quote_identifier(column.name)
        data_type = self._resolve_column_type(schema, column)
        cursor = connection.cursor()
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {data_type}")

    def drop_column(self, schema: CollectionSchema, column_name: str) -> None:
        """컬럼을 삭제한다."""

        if column_name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 삭제할 수 없습니다.")
        connection = self._connection_provider()
        table = self._identifier.quote_table(schema.name)
        cursor = connection.cursor()
        cursor.execute(
            f"ALTER TABLE {table} DROP COLUMN {self._identifier.quote_identifier(column_name)}"
        )

    def _resolve_column_type(self, schema: CollectionSchema, column: ColumnSpec) -> str:
        if column.data_type:
            return column.data_type
        if schema.payload_field and column.name == schema.payload_field:
            return "TEXT"
        return "TEXT"

    def _ensure_no_vector_schema(self, schema: CollectionSchema) -> None:
        if schema.vector_field:
            raise RuntimeError("SQLite 엔진은 벡터 필드를 지원하지 않습니다.")
        if any(column.is_vector for column in schema.columns):
            raise RuntimeError("SQLite 엔진은 벡터 컬럼을 지원하지 않습니다.")
