"""
목적: SQLite 기반 DB 엔진을 제공한다.
설명: 컬렉션 스키마 기반 CRUD와 일반 조회를 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/text_to_sql/integrations/db/base/engine.py
"""

from __future__ import annotations

import re
from typing import List, Optional

from text_to_sql.shared.logging import Logger, create_default_logger
from text_to_sql.integrations.db.base.engine import BaseDBEngine
from text_to_sql.integrations.db.base.models import (
    AggregateQuery,
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
)
from text_to_sql.integrations.db.engines.sql_common import (
    SQLIdentifierHelper,
    ensure_schema,
    payload_field,
    resolve_source,
    select_columns,
    select_sql,
)
from text_to_sql.integrations.db.engines.sqlite.condition_builder import (
    SqliteConditionBuilder,
)
from text_to_sql.integrations.db.engines.sqlite.connection import (
    SqliteConnectionManager,
)
from text_to_sql.integrations.db.engines.sqlite.document_mapper import (
    SqliteDocumentMapper,
)
from text_to_sql.integrations.db.engines.sqlite.schema_manager import (
    SqliteSchemaManager,
)


class SQLiteEngine(BaseDBEngine):
    """SQLite 기반 엔진 구현체."""

    def __init__(
        self,
        database_path: str = "data/db/playground.sqlite",
        logger: Optional[Logger] = None,
    ) -> None:
        self._logger = logger or create_default_logger("SQLiteEngine")
        self._identifier = SQLIdentifierHelper()
        self._connection = SqliteConnectionManager(
            database_path=database_path,
            logger=self._logger,
        )
        self._schema_manager = SqliteSchemaManager(
            connection_provider=self._connection.ensure_connection,
            identifier_helper=self._identifier,
        )
        self._document_mapper = SqliteDocumentMapper()
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

    def aggregate_query(
        self,
        collection: str,
        query: AggregateQuery,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        resolved_schema = ensure_schema(schema, collection)
        table = self._identifier.quote_table(resolved_schema.name)
        params: List[object] = []

        select_parts: List[str] = []
        group_by_parts: List[str] = []
        group_by_fields: set[str] = set()
        aggregate_aliases: dict[str, str] = {}

        for group_by in query.group_by:
            source = resolve_source(group_by.source, group_by.field, resolved_schema)
            if source == FieldSource.PAYLOAD:
                raise ValueError(
                    "SQLite 집계 경로는 payload group_by를 지원하지 않습니다."
                )
            quoted_field = self._identifier.quote_identifier(group_by.field)
            select_parts.append(quoted_field)
            group_by_parts.append(quoted_field)
            group_by_fields.add(group_by.field.lower())

        for aggregate in query.aggregates:
            function_name = aggregate.function.value
            raw_field = str(aggregate.field or "").strip()
            is_count_all = function_name == "COUNT" and raw_field in {"", "*"}
            if is_count_all:
                target_expr = "*"
                default_alias = "count_all"
            else:
                source = resolve_source(aggregate.source, raw_field, resolved_schema)
                if source == FieldSource.PAYLOAD:
                    raise ValueError(
                        "SQLite 집계 경로는 payload 집계를 지원하지 않습니다."
                    )
                target_expr = self._identifier.quote_identifier(raw_field)
                default_alias = f"{function_name.lower()}_{raw_field.lower()}"
            alias = self._normalize_aggregate_alias(aggregate.alias, default_alias)
            aggregate_aliases[alias.lower()] = alias
            select_parts.append(
                f"{function_name}({target_expr}) AS {self._identifier.quote_identifier(alias)}"
            )

        if not select_parts:
            raise ValueError("집계 SELECT 항목이 비어 있습니다.")

        sql = f"SELECT {', '.join(select_parts)} FROM {table}"
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

        if group_by_parts:
            sql += " GROUP BY " + ", ".join(group_by_parts)

        if query.sort:
            order_by_parts = []
            for sort_field in query.sort:
                direction = sort_field.order.value
                sort_key = str(sort_field.field or "").strip()
                alias = aggregate_aliases.get(sort_key.lower())
                if alias:
                    order_by_parts.append(
                        f"{self._identifier.quote_identifier(alias)} {direction}"
                    )
                    continue
                if sort_key.lower() in group_by_fields:
                    order_by_parts.append(
                        f"{self._identifier.quote_identifier(sort_key)} {direction}"
                    )
                    continue
                source = resolve_source(sort_field.source, sort_key, resolved_schema)
                if source == FieldSource.PAYLOAD:
                    raise ValueError(
                        "SQLite 집계 경로는 payload 정렬을 지원하지 않습니다."
                    )
                order_by_parts.append(
                    f"{self._identifier.quote_identifier(sort_key)} {direction}"
                )
            sql += " ORDER BY " + ", ".join(order_by_parts)

        if query.pagination:
            sql += " LIMIT ? OFFSET ?"
            params.extend([query.pagination.limit, query.pagination.offset])

        connection = self._connection.ensure_connection()
        rows = connection.cursor().execute(sql, params).fetchall()
        documents: List[Document] = []
        for index, row in enumerate(rows):
            row_dict = {str(key): value for key, value in dict(row).items()}
            documents.append(
                Document(
                    doc_id=index + 1,
                    fields=row_dict,
                    payload={},
                )
            )
        return documents

    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        raise RuntimeError("SQLite 엔진은 벡터 검색을 지원하지 않습니다.")

    def _normalize_aggregate_alias(
        self,
        raw_alias: object,
        default_alias: str,
    ) -> str:
        candidate = str(raw_alias or "").strip() or default_alias
        sanitized = re.sub(r"[^A-Za-z0-9_]+", "_", candidate).strip("_")
        if not sanitized:
            sanitized = default_alias
        if sanitized[0].isdigit():
            sanitized = f"a_{sanitized}"
        return self._identifier.plain_identifier(sanitized)
