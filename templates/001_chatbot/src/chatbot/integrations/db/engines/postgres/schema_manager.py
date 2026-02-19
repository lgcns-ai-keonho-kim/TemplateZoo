"""
목적: PostgreSQL 스키마 관리 모듈을 제공한다.
설명: 테이블 생성/삭제와 컬럼 추가/삭제를 담당한다.
디자인 패턴: 매니저 패턴
참조: src/chatbot/integrations/db/engines/postgres/vector_store.py
"""

from __future__ import annotations

from chatbot.integrations.db.base.models import CollectionSchema, ColumnSpec
from chatbot.integrations.db.engines.sql_common import (
    SQLIdentifierHelper,
    vector_dimension,
)
from chatbot.integrations.db.engines.postgres.vector_store import (
    PostgresVectorStore,
)


class PostgresSchemaManager:
    """PostgreSQL 스키마 관리자."""

    def __init__(
        self,
        identifier_helper: SQLIdentifierHelper,
        vector_store: PostgresVectorStore,
    ) -> None:
        self._identifier = identifier_helper
        self._vector_store = vector_store

    def create_collection(self, connection, schema: CollectionSchema) -> None:
        """테이블을 생성한다."""

        table = self._identifier.quote_table(schema.name)
        with connection.cursor() as cursor:
            if schema.columns:
                column_defs = []
                has_primary_key = False
                for column in schema.columns:
                    col_name = self._identifier.quote_identifier(column.name)
                    data_type = self._resolve_column_type(schema, column)
                    col_def = f"{col_name} {data_type}"
                    if not column.nullable:
                        col_def += " NOT NULL"
                    if column.is_primary or column.name == schema.primary_key:
                        col_def += " PRIMARY KEY"
                        has_primary_key = True
                    column_defs.append(col_def)
                if not has_primary_key and schema.primary_key in schema.column_names():
                    column_defs.append(
                        f"PRIMARY KEY ({self._identifier.quote_identifier(schema.primary_key)})"
                    )
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
                )
            else:
                column_defs = [f"{self._identifier.quote_identifier(schema.primary_key)} TEXT PRIMARY KEY"]
                if schema.payload_field:
                    column_defs.append(
                        f"{self._identifier.quote_identifier(schema.payload_field)} JSONB"
                    )
                if schema.vector_field:
                    dim = vector_dimension(schema)
                    column_defs.append(
                        f"{self._identifier.quote_identifier(schema.vector_field)} vector({dim})"
                    )
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
                )
            self._vector_store.ensure_vector_extension(cursor, schema)
            self._vector_store.ensure_vector_index(cursor, schema)

    def delete_collection(self, connection, name: str) -> None:
        """테이블을 삭제한다."""

        table = self._identifier.quote_table(name)
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

    def add_column(
        self,
        connection,
        schema: CollectionSchema,
        column: ColumnSpec,
    ) -> None:
        """컬럼을 추가한다."""

        if column.is_primary or column.name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 추가할 수 없습니다.")
        table = self._identifier.quote_table(schema.name)
        column_name = self._identifier.quote_identifier(column.name)
        data_type = self._resolve_column_type(schema, column)
        with connection.cursor() as cursor:
            if column.is_vector or column.name == schema.vector_field:
                self._vector_store.ensure_vector_extension(cursor, schema)
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {data_type}"
            )
            if column.is_vector or column.name == schema.vector_field:
                self._vector_store.ensure_vector_index(cursor, schema)

    def drop_column(
        self,
        connection,
        schema: CollectionSchema,
        column_name: str,
    ) -> None:
        """컬럼을 삭제한다."""

        if column_name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 삭제할 수 없습니다.")
        table = self._identifier.quote_table(schema.name)
        with connection.cursor() as cursor:
            self._vector_store.drop_vector_index_if_needed(cursor, schema, column_name)
            cursor.execute(
                f"ALTER TABLE {table} DROP COLUMN IF EXISTS {self._identifier.quote_identifier(column_name)}"
            )

    def _resolve_column_type(self, schema: CollectionSchema, column: ColumnSpec) -> str:
        if column.data_type:
            return column.data_type
        if schema.payload_field and column.name == schema.payload_field:
            return "JSONB"
        if column.is_vector or column.name == schema.vector_field:
            return f"vector({vector_dimension(schema)})"
        return "TEXT"
