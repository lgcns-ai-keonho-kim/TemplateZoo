"""
목적: SQLite 벡터 저장 모듈을 제공한다.
설명: sqlite-vec 테이블 관리, 벡터 저장/조회/검색을 담당한다.
디자인 패턴: 저장소 패턴
참조: src/rag_chatbot/integrations/db/engines/sqlite/vector_codec.py
"""

from __future__ import annotations

import sqlite3
from typing import Callable, Dict, Optional, Tuple

from rag_chatbot.integrations.db.base.models import (
    CollectionSchema,
    Vector,
    VectorSearchRequest,
)
from rag_chatbot.integrations.db.engines.sql_common import (
    SQLIdentifierHelper,
    vector_dimension,
    vector_field,
)
from rag_chatbot.integrations.db.engines.sqlite.vector_codec import SqliteVectorCodec


class SqliteVectorStore:
    """SQLite 벡터 저장소."""

    def __init__(
        self,
        connection_provider: Callable[[], sqlite3.Connection],
        identifier_helper: SQLIdentifierHelper,
        vector_codec: SqliteVectorCodec,
        enable_vector: bool,
    ) -> None:
        self._connection_provider = connection_provider
        self._identifier = identifier_helper
        self._vector_codec = vector_codec
        self._enable_vector = enable_vector
        self._vector_tables: Dict[Tuple[str, str], str] = {}

    def create_vector_table(
        self,
        schema: CollectionSchema,
        target_field: Optional[str] = None,
    ) -> None:
        """벡터 테이블을 생성한다."""

        field = target_field or vector_field(schema)
        if not field:
            return
        self._ensure_enabled()
        connection = self._connection_provider()
        dim = vector_dimension(schema)
        table = self._vector_table(schema, field)
        cursor = connection.cursor()
        cursor.execute(
            " ".join(
                [
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS {self._identifier.quote_identifier(table)}",
                    "USING vec0(",
                    f"{self._identifier.plain_identifier(schema.primary_key)} TEXT,",
                    f"{self._identifier.plain_identifier(field)} float[{dim}]",
                    ")",
                ]
            )
        )
        self._vector_tables[(schema.name, field)] = table

    def drop_vector_table(
        self,
        schema: CollectionSchema,
        target_field: Optional[str] = None,
    ) -> None:
        """스키마 기준 벡터 테이블을 삭제한다."""

        field = target_field or vector_field(schema)
        if not field:
            return
        connection = self._connection_provider()
        table = self._vector_table(schema, field)
        cursor = connection.cursor()
        cursor.execute(
            f"DROP TABLE IF EXISTS {self._identifier.quote_identifier(table)}"
        )
        self._vector_tables.pop((schema.name, field), None)

    def drop_vector_table_by_collection(self, collection: str) -> None:
        """컬렉션 기준 벡터 테이블을 삭제한다."""

        if not self._enable_vector:
            return
        connection = self._connection_provider()
        cursor = connection.cursor()

        for (name, _field), table in list(self._vector_tables.items()):
            if name != collection:
                continue
            cursor.execute(
                f"DROP TABLE IF EXISTS {self._identifier.quote_identifier(table)}"
            )
            self._vector_tables.pop((name, _field), None)

        cursor.execute(
            f"DROP TABLE IF EXISTS {self._identifier.quote_identifier(f'vec_{collection}')}"
        )

    def upsert_vector(
        self,
        schema: CollectionSchema,
        doc_id: object,
        values: list[float],
        target_field: Optional[str] = None,
    ) -> None:
        """문서 벡터를 저장한다."""

        self._ensure_enabled()
        field = target_field or vector_field(schema)
        if not field:
            return
        connection = self._connection_provider()
        table = self._vector_table(schema, field)
        serialized = self._vector_codec.serialize(values)
        cursor = connection.cursor()
        cursor.execute(
            " ".join(
                [
                    f"DELETE FROM {self._identifier.quote_identifier(table)}",
                    f"WHERE {self._identifier.quote_identifier(schema.primary_key)} = ?",
                ]
            ),
            (doc_id,),
        )
        cursor.execute(
            " ".join(
                [
                    f"INSERT OR REPLACE INTO {self._identifier.quote_identifier(table)}",
                    f"({self._identifier.quote_identifier(schema.primary_key)}, {self._identifier.quote_identifier(field)})",
                    "VALUES (?, ?)",
                ]
            ),
            (doc_id, serialized),
        )

    def delete_vector(
        self,
        schema: CollectionSchema,
        doc_id: object,
        target_field: Optional[str] = None,
    ) -> None:
        """문서 벡터를 삭제한다."""

        if not self._enable_vector:
            return
        field = target_field or vector_field(schema)
        if not field:
            return
        connection = self._connection_provider()
        table = self._vector_table(schema, field)
        cursor = connection.cursor()
        cursor.execute(
            f"DELETE FROM {self._identifier.quote_identifier(table)} "
            f"WHERE {self._identifier.quote_identifier(schema.primary_key)} = ?",
            (doc_id,),
        )

    def search(
        self,
        request: VectorSearchRequest,
        schema: CollectionSchema,
    ) -> list[tuple]:
        """벡터 유사도 검색을 수행한다."""

        field = request.vector_field or vector_field(schema)
        if not field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        self._ensure_enabled()
        connection = self._connection_provider()
        table = self._vector_table(schema, field)
        vector_param = self._vector_codec.serialize(request.vector.values)
        cursor = connection.cursor()
        return cursor.execute(
            " ".join(
                [
                    f"SELECT {self._identifier.quote_identifier(schema.primary_key)}, distance FROM {self._identifier.quote_identifier(table)}",
                    f"WHERE {self._identifier.quote_identifier(field)} MATCH ?",
                    "AND k = ?",
                ]
            ),
            (vector_param, request.top_k),
        ).fetchall()

    def load_vector(
        self,
        schema: CollectionSchema,
        doc_id: object,
        target_field: Optional[str] = None,
    ) -> Optional[Vector]:
        """문서 ID로 벡터를 조회한다."""

        field = target_field or vector_field(schema)
        if not field or not self._enable_vector:
            return None
        connection = self._connection_provider()
        table = self._vector_table(schema, field)
        cursor = connection.cursor()
        row = cursor.execute(
            " ".join(
                [
                    f"SELECT {self._identifier.quote_identifier(field)} FROM {self._identifier.quote_identifier(table)}",
                    f"WHERE {self._identifier.quote_identifier(schema.primary_key)} = ?",
                ]
            ),
            (doc_id,),
        ).fetchone()
        if row is None:
            return None
        values = self._vector_codec.deserialize(row[0], vector_dimension(schema))
        if values is None:
            return None
        return Vector(values=values, dimension=len(values))

    def _vector_table(self, schema: CollectionSchema, field: str) -> str:
        mapped = self._vector_tables.get((schema.name, field))
        if mapped:
            return mapped
        if field == schema.vector_field and schema.vector_table:
            return schema.vector_table
        return f"vec_{schema.name}_{field}"

    def _ensure_enabled(self) -> None:
        if not self._enable_vector:
            raise RuntimeError("벡터 저장이 비활성화되었습니다.")
