"""
목적: SQLite 기반 DB 엔진을 제공한다.
설명: 컬렉션 스키마 기반 CRUD와 sqlite-vec 벡터 검색을 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/rag_chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

import json
from typing import List, Optional

from rag_chatbot.shared.logging import Logger, create_default_logger
from rag_chatbot.integrations.db.base.engine import BaseDBEngine
from rag_chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    Query,
    Vector,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from rag_chatbot.integrations.db.engines.sql_common import (
    SQLIdentifierHelper,
    ensure_schema,
    payload_field,
    resolve_source,
    select_columns,
    select_sql,
    vector_field,
)
from rag_chatbot.integrations.db.engines.sqlite.condition_builder import (
    SqliteConditionBuilder,
)
from rag_chatbot.integrations.db.engines.sqlite.connection import (
    SqliteConnectionManager,
)
from rag_chatbot.integrations.db.engines.sqlite.document_mapper import (
    SqliteDocumentMapper,
)
from rag_chatbot.integrations.db.engines.sqlite.schema_manager import (
    SqliteSchemaManager,
)
from rag_chatbot.integrations.db.engines.sqlite.vector_codec import SqliteVectorCodec
from rag_chatbot.integrations.db.engines.sqlite.vector_store import SqliteVectorStore

try:
    import sqlite_vec
except ImportError:  # pragma: no cover - 환경 의존 로딩
    sqlite_vec = None


class SQLiteEngine(BaseDBEngine):
    """sqlite-vec 기반 SQLite 엔진 구현체."""

    def __init__(
        self,
        database_path: str = "data/db/playground.sqlite",
        logger: Optional[Logger] = None,
        enable_vector: bool = True,
    ) -> None:
        self._logger = logger or create_default_logger("SQLiteEngine")
        self._enable_vector = enable_vector
        self._identifier = SQLIdentifierHelper()
        self._vector_codec = SqliteVectorCodec(sqlite_vec)
        self._connection = SqliteConnectionManager(
            database_path=database_path,
            logger=self._logger,
            enable_vector=enable_vector,
            sqlite_vec_module=sqlite_vec,
        )
        self._vector_store = SqliteVectorStore(
            connection_provider=self._connection.ensure_connection,
            identifier_helper=self._identifier,
            vector_codec=self._vector_codec,
            enable_vector=enable_vector,
        )
        self._schema_manager = SqliteSchemaManager(
            connection_provider=self._connection.ensure_connection,
            identifier_helper=self._identifier,
            vector_store=self._vector_store,
            enable_vector=enable_vector,
        )
        self._document_mapper = SqliteDocumentMapper(self._vector_store.load_vector)
        self._condition_builder = SqliteConditionBuilder(self._identifier)

    @property
    def name(self) -> str:
        return "sqlite"

    @property
    def supports_vector_search(self) -> bool:
        return self._connection.supports_vector_search

    def connect(self) -> None:
        self._connection.connect()

    def close(self) -> None:
        self._connection.close()

    def create_collection(self, schema: CollectionSchema) -> None:
        schema = ensure_schema(schema)
        self._schema_manager.create_collection(schema)
        self._connection.ensure_connection().commit()

    def delete_collection(self, name: str) -> None:
        self._schema_manager.delete_collection(name)
        self._connection.ensure_connection().commit()

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        self._schema_manager.add_column(resolved_schema, column)
        self._connection.ensure_connection().commit()

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        self._schema_manager.drop_column(resolved_schema, column_name)
        self._connection.ensure_connection().commit()

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        connection = self._connection.ensure_connection()
        table = self._identifier.quote_table(resolved_schema.name)
        cursor = connection.cursor()
        target_vector_field = vector_field(resolved_schema)
        additional_vector_fields = [
            column.name
            for column in resolved_schema.columns
            if column.is_vector and column.name != target_vector_field
        ]
        for document in documents:
            row = self._document_mapper.document_to_row(document, resolved_schema)
            if not row:
                continue
            columns = list(row.keys())
            placeholders = ", ".join(["?"] * len(columns))
            column_sql = ", ".join(
                self._identifier.quote_identifier(column) for column in columns
            )
            cursor.execute(
                f"INSERT OR REPLACE INTO {table} ({column_sql}) VALUES ({placeholders})",
                list(row.values()),
            )
            if target_vector_field and document.vector:
                if document.vector.dimension is None:
                    vector = Vector(
                        values=document.vector.values,
                        dimension=len(document.vector.values),
                    )
                else:
                    vector = document.vector
                self._vector_store.upsert_vector(
                    resolved_schema,
                    document.doc_id,
                    vector.values,
                )
            for field_name in additional_vector_fields:
                vector_values = self._coerce_vector_values(document.fields.get(field_name))
                if vector_values is None:
                    continue
                self._vector_store.upsert_vector(
                    resolved_schema,
                    document.doc_id,
                    vector_values,
                    target_field=field_name,
                )
        connection.commit()

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        resolved_schema = ensure_schema(schema, collection)
        table = self._identifier.quote_table(resolved_schema.name)
        columns = select_columns(resolved_schema)
        select_clause = select_sql(columns, self._identifier.quote_identifier)
        primary_key = self._identifier.quote_identifier(resolved_schema.primary_key)
        connection = self._connection.ensure_connection()
        cursor = connection.cursor()
        row = cursor.execute(
            f"SELECT {select_clause} FROM {table} WHERE {primary_key} = ?",
            (doc_id,),
        ).fetchone()
        if row is None:
            return None
        return self._document_mapper.row_to_document(dict(row), resolved_schema)

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        table = self._identifier.quote_table(resolved_schema.name)
        primary_key = self._identifier.quote_identifier(resolved_schema.primary_key)
        connection = self._connection.ensure_connection()
        cursor = connection.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE {primary_key} = ?", (doc_id,))
        self._vector_store.delete_vector(resolved_schema, doc_id)
        for column in resolved_schema.columns:
            if not column.is_vector:
                continue
            if column.name == vector_field(resolved_schema):
                continue
            self._vector_store.delete_vector(
                resolved_schema,
                doc_id,
                target_field=column.name,
            )
        connection.commit()

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        resolved_schema = ensure_schema(schema, collection)
        table = self._identifier.quote_table(resolved_schema.name)
        columns = select_columns(resolved_schema)
        select_clause = select_sql(columns, self._identifier.quote_identifier)
        sql = f"SELECT {select_clause} FROM {table}"
        params: List[object] = []
        if query.filter_expression and query.filter_expression.conditions:
            clauses = []
            for condition in query.filter_expression.conditions:
                clause, clause_params = self._condition_builder.build(
                    condition,
                    resolved_schema,
                )
                clauses.append(clause)
                params.extend(clause_params)
            joiner = " OR " if query.filter_expression.logic == "OR" else " AND "
            sql += " WHERE " + joiner.join(clauses)
        if query.sort:
            order_by_parts = []
            for sort_field in query.sort:
                order = sort_field.order.value
                source = resolve_source(
                    sort_field.source,
                    sort_field.field,
                    resolved_schema,
                )
                if source == FieldSource.PAYLOAD:
                    payload = payload_field(resolved_schema)
                    order_by_parts.append(
                        f"json_extract({self._identifier.quote_identifier(payload)}, '$.{sort_field.field}') {order}"
                    )
                else:
                    order_by_parts.append(
                        f"{self._identifier.quote_identifier(sort_field.field)} {order}"
                    )
            sql += " ORDER BY " + ", ".join(order_by_parts)
        if query.pagination:
            sql += " LIMIT ? OFFSET ?"
            params.extend([query.pagination.limit, query.pagination.offset])
        connection = self._connection.ensure_connection()
        rows = connection.cursor().execute(sql, params).fetchall()
        return [
            self._document_mapper.row_to_document(dict(row), resolved_schema)
            for row in rows
        ]

    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        resolved_schema = ensure_schema(schema, request.collection)
        target_vector_field = request.vector_field or vector_field(resolved_schema)
        if not target_vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        if not self._enable_vector:
            raise RuntimeError("벡터 검색이 비활성화되었습니다.")
        rows = self._vector_store.search(request, resolved_schema)
        results: List[VectorSearchResult] = []
        for row in rows:
            doc_id = row[0]
            document = self.get(request.collection, doc_id, resolved_schema)
            if document is None:
                continue
            if request.filter_expression and not self._condition_builder.match_filter(
                document,
                request.filter_expression,
                resolved_schema,
            ):
                continue
            if not request.include_vectors:
                document.vector = None
            results.append(
                VectorSearchResult(document=document, score=float(row[1]))
            )
        return VectorSearchResponse(results=results, total=len(results))

    def _coerce_vector_values(self, value: object) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, Vector):
            return [float(item) for item in value.values]
        if isinstance(value, list):
            if not value:
                return None
            try:
                return [float(item) for item in value]
            except (TypeError, ValueError):
                return None
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError:
                return None
            if not isinstance(decoded, list) or not decoded:
                return None
            try:
                return [float(item) for item in decoded]
            except (TypeError, ValueError):
                return None
        return None
