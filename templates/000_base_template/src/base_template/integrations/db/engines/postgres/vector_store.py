"""
목적: PostgreSQL 벡터 관리 모듈을 제공한다.
설명: PGVector 확장/인덱스 생성과 벡터 컬럼 유효성 판단을 담당한다.
디자인 패턴: 매니저 패턴
참조: src/base_template/integrations/db/engines/postgres/vector_adapter.py
"""

from __future__ import annotations

from base_template.integrations.db.base.models import CollectionSchema
from base_template.integrations.db.engines.sql_common import (
    SQLIdentifierHelper,
    vector_field,
)
from base_template.integrations.db.engines.postgres.vector_adapter import (
    PostgresVectorAdapter,
)


class PostgresVectorStore:
    """PostgreSQL 벡터 관리 컴포넌트."""

    def __init__(
        self,
        identifier_helper: SQLIdentifierHelper,
        vector_adapter: PostgresVectorAdapter,
    ) -> None:
        self._identifier = identifier_helper
        self._vector_adapter = vector_adapter

    @property
    def adapter(self) -> PostgresVectorAdapter:
        """벡터 어댑터를 반환한다."""

        return self._vector_adapter

    def has_vector_column(self, schema: CollectionSchema) -> bool:
        """스키마에 벡터 컬럼이 존재하는지 반환한다."""

        if not schema.vector_field:
            return False
        if not schema.columns:
            return True
        if schema.vector_field in schema.column_names():
            return True
        return any(column.is_vector for column in schema.columns)

    def ensure_vector_extension(self, cursor, schema: CollectionSchema) -> None:
        """벡터 컬럼이 필요하면 확장을 준비한다."""

        if self.has_vector_column(schema):
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

    def ensure_vector_index(self, cursor, schema: CollectionSchema) -> None:
        """벡터 컬럼 인덱스를 준비한다."""

        target_vector_field = vector_field(schema)
        if not target_vector_field or not self.has_vector_column(schema):
            return
        index_name = f"{schema.name}_{target_vector_field}_vec_idx"
        table = self._identifier.quote_table(schema.name)
        vector_col = self._identifier.quote_identifier(target_vector_field)
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {self._identifier.quote_identifier(index_name)} "
            f"ON {table} USING ivfflat ({vector_col} vector_cosine_ops)"
        )

    def drop_vector_index_if_needed(
        self,
        cursor,
        schema: CollectionSchema,
        column_name: str,
    ) -> None:
        """벡터 컬럼 삭제 시 인덱스를 함께 정리한다."""

        if column_name != schema.vector_field or not self.has_vector_column(schema):
            return
        index_name = f"{schema.name}_{column_name}_vec_idx"
        cursor.execute(
            f"DROP INDEX IF EXISTS {self._identifier.quote_identifier(index_name)}"
        )
