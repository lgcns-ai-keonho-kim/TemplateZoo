"""
목적: PostgreSQL 기반 DB 엔진을 제공한다.
설명: 컬렉션 스키마 기반 CRUD와 PGVector 벡터 검색을 처리한다.
디자인 패턴: 어댑터 패턴
참조: src/rag_chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from rag_chatbot.shared.logging import Logger, create_default_logger
from rag_chatbot.integrations.db.base.engine import BaseDBEngine
from rag_chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    Query,
    SortOrder,
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
from rag_chatbot.integrations.db.engines.postgres.condition_builder import (
    PostgresConditionBuilder,
)
from rag_chatbot.integrations.db.engines.postgres.connection import (
    PostgresConnectionManager,
)
from rag_chatbot.integrations.db.engines.postgres.document_mapper import (
    PostgresDocumentMapper,
)
from rag_chatbot.integrations.db.engines.postgres.schema_manager import (
    PostgresSchemaManager,
)
from rag_chatbot.integrations.db.engines.postgres.vector_adapter import (
    PostgresVectorAdapter,
)
from rag_chatbot.integrations.db.engines.postgres.vector_store import (
    PostgresVectorStore,
)

try:
    import psycopg2
    from psycopg2.extras import Json as PgJson
except ImportError:  # pragma: no cover - 환경 의존 로딩
    psycopg2 = None
    PgJson = None

try:
    from pgvector.psycopg2 import register_vector as register_pgvector
    from pgvector import Vector as PgVector
except ImportError:  # pragma: no cover - 환경 의존 로딩
    register_pgvector = None
    PgVector = None


class PostgresEngine(BaseDBEngine):
    """PostgreSQL 기반 엔진 구현체."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        host: str = "127.0.0.1",
        port: int = 5432,
        user: str = "postgres",
        password: Optional[str] = None,
        database: str = "postgres",
        scheme: str = "postgresql",
        logger: Optional[Logger] = None,
    ) -> None:
        if not dsn:
            auth = f"{user}"
            if password:
                auth = f"{auth}:{password}"
            dsn = f"{scheme}://{auth}@{host}:{port}/{database}"
        self._logger = logger or create_default_logger("PostgresEngine")
        self._dsn = dsn
        self._identifier = SQLIdentifierHelper()
        self._vector_adapter = PostgresVectorAdapter(register_pgvector, PgVector)
        self._vector_store = PostgresVectorStore(self._identifier, self._vector_adapter)
        self._connection = PostgresConnectionManager(
            dsn=self._dsn,
            logger=self._logger,
            psycopg2_module=psycopg2,
            vector_adapter=self._vector_adapter,
        )
        self._schema_manager = PostgresSchemaManager(
            identifier_helper=self._identifier,
            vector_store=self._vector_store,
        )
        self._condition_builder = PostgresConditionBuilder(self._identifier)
        self._document_mapper = PostgresDocumentMapper(
            vector_adapter=self._vector_store.adapter,
            json_value_encoder=self._json_value,
        )

    @property
    def name(self) -> str:
        return "postgres"

    @property
    def supports_vector_search(self) -> bool:
        return True

    def connect(self) -> None:
        self._connection.connect()

    def close(self) -> None:
        self._connection.close()

    def create_collection(self, schema: CollectionSchema) -> None:
        resolved_schema = ensure_schema(schema)
        connection = self._connection.ensure_connection()
        self._schema_manager.create_collection(connection, resolved_schema)
        connection.commit()
        self._logger.info(f"PostgreSQL 테이블 생성 완료: {resolved_schema.name}")

    def delete_collection(self, name: str) -> None:
        connection = self._connection.ensure_connection()
        self._schema_manager.delete_collection(connection, name)
        connection.commit()
        self._logger.info(f"PostgreSQL 테이블 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        connection = self._connection.ensure_connection()
        self._schema_manager.add_column(connection, resolved_schema, column)
        connection.commit()

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        connection = self._connection.ensure_connection()
        self._schema_manager.drop_column(connection, resolved_schema, column_name)
        connection.commit()

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        table = self._identifier.quote_table(resolved_schema.name)
        connection = self._connection.ensure_connection()
        with connection.cursor() as cursor:
            for document in documents:
                row = self._document_mapper.document_to_row(document, resolved_schema)
                if not row:
                    continue
                columns = list(row.keys())
                placeholders = ", ".join(["%s"] * len(columns))
                column_sql = ", ".join(
                    self._identifier.quote_identifier(col) for col in columns
                )
                update_columns = [c for c in columns if c != resolved_schema.primary_key]
                if update_columns:
                    update_sql = ", ".join(
                        f"{self._identifier.quote_identifier(col)} = EXCLUDED.{self._identifier.quote_identifier(col)}"
                        for col in update_columns
                    )
                    sql = (
                        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) "
                        f"ON CONFLICT ({self._identifier.quote_identifier(resolved_schema.primary_key)}) "
                        f"DO UPDATE SET {update_sql}"
                    )
                else:
                    sql = (
                        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) "
                        f"ON CONFLICT ({self._identifier.quote_identifier(resolved_schema.primary_key)}) DO NOTHING"
                    )
                cursor.execute(sql, list(row.values()))
        connection.commit()

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        resolved_schema = ensure_schema(schema, collection)
        table = self._identifier.quote_table(resolved_schema.name)
        columns = select_columns(resolved_schema, include_vector=True)
        select_clause = select_sql(columns, self._identifier.quote_identifier)
        primary_key = self._identifier.quote_identifier(resolved_schema.primary_key)
        connection = self._connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {select_clause} FROM {table} WHERE {primary_key} = %s",
                (doc_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            row_dict = self._row_to_dict(cursor, row)
        return self._document_mapper.row_to_document(row_dict, resolved_schema)

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
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE {primary_key} = %s", (doc_id,))
        connection.commit()

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        resolved_schema = ensure_schema(schema, collection)
        table = self._identifier.quote_table(resolved_schema.name)
        columns = select_columns(resolved_schema, include_vector=True)
        select_clause = select_sql(columns, self._identifier.quote_identifier)
        params: List[object] = []
        where_sql = ""
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
            where_sql = " WHERE " + joiner.join(clauses)
        order_sql = ""
        if query.sort:
            order_by_parts = []
            for sort_field in query.sort:
                order = "ASC" if sort_field.order == SortOrder.ASC else "DESC"
                source = resolve_source(
                    sort_field.source,
                    sort_field.field,
                    resolved_schema,
                )
                if source == FieldSource.PAYLOAD:
                    payload = payload_field(resolved_schema)
                    order_by_parts.append(
                        f"{self._identifier.quote_identifier(payload)} ->> '{sort_field.field}' {order}"
                    )
                else:
                    order_by_parts.append(
                        f"{self._identifier.quote_identifier(sort_field.field)} {order}"
                    )
            order_sql = " ORDER BY " + ", ".join(order_by_parts)
        limit_sql = ""
        if query.pagination:
            limit_sql = " LIMIT %s OFFSET %s"
            params.extend([query.pagination.limit, query.pagination.offset])
        connection = self._connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {select_clause} FROM {table}{where_sql}{order_sql}{limit_sql}",
                params,
            )
            rows = cursor.fetchall()
            row_dicts = [self._row_to_dict(cursor, row) for row in rows]
        return [
            self._document_mapper.row_to_document(row, resolved_schema)
            for row in row_dicts
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
        table = self._identifier.quote_table(resolved_schema.name)
        vector_col = self._identifier.quote_identifier(target_vector_field)
        columns = select_columns(resolved_schema, include_vector=True)
        select_clause = select_sql(columns, self._identifier.quote_identifier)
        params: List[object] = []
        where_sql = ""
        if request.filter_expression and request.filter_expression.conditions:
            clauses = []
            for condition in request.filter_expression.conditions:
                clause, clause_params = self._condition_builder.build(
                    condition,
                    resolved_schema,
                )
                clauses.append(clause)
                params.extend(clause_params)
            joiner = " OR " if request.filter_expression.logic == "OR" else " AND "
            where_sql = " WHERE " + joiner.join(clauses)
        connection = self._connection.ensure_connection()
        with connection.cursor() as cursor:
            vector_param = self._vector_store.adapter.param(request.vector.values)
            distance_expr = self._vector_store.adapter.distance_expr(vector_col)
            order_expr = distance_expr
            cursor.execute(
                " ".join(
                    [
                        f"SELECT {select_clause}, {distance_expr} AS distance",
                        f"FROM {table}",
                        where_sql,
                        f"ORDER BY {order_expr}",
                        "LIMIT %s",
                    ]
                ),
                params + [vector_param, vector_param, request.top_k],
            )
            rows = cursor.fetchall()
            row_dicts = [self._row_to_dict(cursor, row) for row in rows]
        results: List[VectorSearchResult] = []
        for row in row_dicts:
            distance = row.pop("distance", None)
            document = self._document_mapper.row_to_document(row, resolved_schema)
            if not request.include_vectors:
                document.vector = None
            results.append(
                VectorSearchResult(
                    document=document,
                    score=float(distance) if distance is not None else 0.0,
                )
            )
        return VectorSearchResponse(results=results, total=len(results))

    def _row_to_dict(self, cursor, row: Tuple[Any, ...]) -> Dict[str, Any]:
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))

    def _json_value(self, payload: Dict[str, Any]) -> object:
        if PgJson is not None:
            return PgJson(payload)
        return json.dumps(payload)
