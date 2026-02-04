"""
목적: PostgreSQL 기반 DB 엔진을 제공한다.
설명: 컬렉션 스키마 기반 CRUD와 PGVector 벡터 검색을 처리한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/integrations/db/base/engine.py
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from ....shared.logging import Logger, create_default_logger
from ..base.engine import BaseDBEngine
from ..base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    Query,
    SortOrder,
    Vector,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)

try:
    import psycopg2
    from psycopg2.extras import Json as PgJson
except ImportError:  # pragma: no cover - 환경 의존 로딩
    psycopg2 = None
    PgJson = None

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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
        self._dsn = dsn
        self._logger = logger or create_default_logger("PostgresEngine")
        self._connection = None

    @property
    def name(self) -> str:
        return "postgres"

    @property
    def supports_vector_search(self) -> bool:
        return True

    def connect(self) -> None:
        if psycopg2 is None:
            raise RuntimeError("psycopg2-binary 패키지가 설치되어 있지 않습니다.")
        if self._connection is not None:
            return
        self._connection = psycopg2.connect(self._dsn)
        self._logger.info("PostgreSQL 연결이 초기화되었습니다.")

    def close(self) -> None:
        if self._connection is None:
            return
        self._connection.close()
        self._connection = None
        self._logger.info("PostgreSQL 연결이 종료되었습니다.")

    def create_collection(self, schema: CollectionSchema) -> None:
        self._ensure_connection()
        schema = self._ensure_schema(schema)
        table = self._quote_table(schema.name)
        with self._connection.cursor() as cursor:
            if schema.columns:
                column_defs = []
                has_pk = False
                for column in schema.columns:
                    col_name = self._quote_identifier(column.name)
                    data_type = self._resolve_column_type(schema, column)
                    col_def = f"{col_name} {data_type}"
                    if not column.nullable:
                        col_def += " NOT NULL"
                    if column.is_primary or column.name == schema.primary_key:
                        col_def += " PRIMARY KEY"
                        has_pk = True
                    column_defs.append(col_def)
                if not has_pk and schema.primary_key in schema.column_names():
                    column_defs.append(
                        f'PRIMARY KEY ("{schema.primary_key}")'
                    )
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
                )
            else:
                column_defs = [f'{self._quote_identifier(schema.primary_key)} TEXT PRIMARY KEY']
                if schema.payload_field:
                    column_defs.append(
                        f'{self._quote_identifier(schema.payload_field)} JSONB'
                    )
                vector_field = self._vector_field(schema)
                if vector_field:
                    vector_dim = self._vector_dimension(schema)
                    column_defs.append(
                        f'{self._quote_identifier(vector_field)} vector({vector_dim})'
                    )
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
                )
            self._ensure_vector_extension(cursor, schema)
            self._ensure_vector_index(cursor, schema)
        self._connection.commit()
        self._logger.info(f"PostgreSQL 테이블 생성 완료: {schema.name}")

    def delete_collection(self, name: str) -> None:
        self._ensure_connection()
        table = self._quote_table(name)
        with self._connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        self._connection.commit()
        self._logger.info(f"PostgreSQL 테이블 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_connection()
        schema = self._ensure_schema(schema, collection)
        if column.is_primary or column.name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 추가할 수 없습니다.")
        table = self._quote_table(schema.name)
        column_name = self._quote_identifier(column.name)
        data_type = self._resolve_column_type(schema, column)
        with self._connection.cursor() as cursor:
            if column.is_vector or column.name == schema.vector_field:
                self._ensure_vector_extension(cursor, schema)
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_name} {data_type}"
            )
            if column.is_vector or column.name == schema.vector_field:
                self._ensure_vector_index(cursor, schema)
        self._connection.commit()

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_connection()
        schema = self._ensure_schema(schema, collection)
        if column_name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 삭제할 수 없습니다.")
        table = self._quote_table(schema.name)
        with self._connection.cursor() as cursor:
            if column_name == schema.vector_field and self._has_vector_column(schema):
                index_name = f"{schema.name}_{column_name}_vec_idx"
                cursor.execute(
                    f"DROP INDEX IF EXISTS {self._quote_identifier(index_name)}"
                )
            cursor.execute(
                f"ALTER TABLE {table} DROP COLUMN IF EXISTS {self._quote_identifier(column_name)}"
            )
        self._connection.commit()

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_connection()
        schema = self._ensure_schema(schema, collection)
        table = self._quote_table(schema.name)
        with self._connection.cursor() as cursor:
            for document in documents:
                row = self._document_to_row(document, schema)
                if not row:
                    continue
                columns = list(row.keys())
                placeholders = ", ".join(["%s"] * len(columns))
                column_sql = ", ".join(self._quote_identifier(col) for col in columns)
                update_columns = [c for c in columns if c != schema.primary_key]
                if update_columns:
                    update_sql = ", ".join(
                        f"{self._quote_identifier(col)} = EXCLUDED.{self._quote_identifier(col)}"
                        for col in update_columns
                    )
                    sql = (
                        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) "
                        f"ON CONFLICT ({self._quote_identifier(schema.primary_key)}) "
                        f"DO UPDATE SET {update_sql}"
                    )
                else:
                    sql = (
                        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) "
                        f"ON CONFLICT ({self._quote_identifier(schema.primary_key)}) DO NOTHING"
                    )
                cursor.execute(sql, list(row.values()))
        self._connection.commit()

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        self._ensure_connection()
        schema = self._ensure_schema(schema, collection)
        table = self._quote_table(schema.name)
        columns = self._select_columns(schema)
        select_sql = self._select_sql(columns)
        pk = self._quote_identifier(schema.primary_key)
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {select_sql} FROM {table} WHERE {pk} = %s",
                (doc_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            row_dict = self._row_to_dict(cursor, row)
        return self._row_to_document(row_dict, schema)

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_connection()
        schema = self._ensure_schema(schema, collection)
        table = self._quote_table(schema.name)
        pk = self._quote_identifier(schema.primary_key)
        with self._connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE {pk} = %s", (doc_id,))
        self._connection.commit()

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        self._ensure_connection()
        schema = self._ensure_schema(schema, collection)
        table = self._quote_table(schema.name)
        columns = self._select_columns(schema)
        select_sql = self._select_sql(columns)
        params: List[object] = []
        where_sql = ""
        if query.filter_expression and query.filter_expression.conditions:
            clauses = []
            for condition in query.filter_expression.conditions:
                clause, clause_params = self._build_condition(condition, schema)
                clauses.append(clause)
                params.extend(clause_params)
            joiner = " OR " if query.filter_expression.logic == "OR" else " AND "
            where_sql = " WHERE " + joiner.join(clauses)
        order_sql = ""
        if query.sort:
            order_by_parts = []
            for sort_field in query.sort:
                order = "ASC" if sort_field.order == SortOrder.ASC else "DESC"
                source = self._resolve_source(sort_field.source, sort_field.field, schema)
                if source == FieldSource.PAYLOAD:
                    payload_field = self._payload_field(schema)
                    order_by_parts.append(
                        f"{self._quote_identifier(payload_field)} ->> '{sort_field.field}' {order}"
                    )
                else:
                    order_by_parts.append(
                        f"{self._quote_identifier(sort_field.field)} {order}"
                    )
            order_sql = " ORDER BY " + ", ".join(order_by_parts)
        limit_sql = ""
        if query.pagination:
            limit_sql = " LIMIT %s OFFSET %s"
            params.extend([query.pagination.limit, query.pagination.offset])
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {select_sql} FROM {table}{where_sql}{order_sql}{limit_sql}",
                params,
            )
            rows = cursor.fetchall()
            row_dicts = [self._row_to_dict(cursor, row) for row in rows]
        return [self._row_to_document(row, schema) for row in row_dicts]

    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        self._ensure_connection()
        schema = self._ensure_schema(schema, request.collection)
        vector_field = self._vector_field(schema)
        if not vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        table = self._quote_table(schema.name)
        vector_col = self._quote_identifier(vector_field)
        columns = self._select_columns(schema)
        select_sql = self._select_sql(columns)
        params: List[object] = []
        where_sql = ""
        if request.filter_expression and request.filter_expression.conditions:
            clauses = []
            for condition in request.filter_expression.conditions:
                clause, clause_params = self._build_condition(condition, schema)
                clauses.append(clause)
                params.extend(clause_params)
            joiner = " OR " if request.filter_expression.logic == "OR" else " AND "
            where_sql = " WHERE " + joiner.join(clauses)
        with self._connection.cursor() as cursor:
            cursor.execute(
                " ".join(
                    [
                        f"SELECT {select_sql}, {vector_col} <-> %s AS distance",
                        f"FROM {table}",
                        where_sql,
                        f"ORDER BY {vector_col} <-> %s",
                        "LIMIT %s",
                    ]
                ),
                params + [request.vector.values, request.vector.values, request.top_k],
            )
            rows = cursor.fetchall()
            row_dicts = [self._row_to_dict(cursor, row) for row in rows]
        results: List[VectorSearchResult] = []
        for row in row_dicts:
            distance = row.pop("distance", None)
            document = self._row_to_document(row, schema)
            if not request.include_vectors:
                document.vector = None
            results.append(
                VectorSearchResult(
                    document=document,
                    score=float(distance) if distance is not None else 0.0,
                )
            )
        return VectorSearchResponse(results=results, total=len(results))

    def _document_to_row(
        self, document: Document, schema: CollectionSchema
    ) -> Dict[str, Any]:
        row: Dict[str, Any] = {schema.primary_key: document.doc_id}
        if schema.payload_field:
            row[schema.payload_field] = self._json_value(document.payload)
        for key, value in document.fields.items():
            row[key] = value
        vector_field = self._vector_field(schema)
        if vector_field and document.vector:
            row[vector_field] = document.vector.values
        if schema.columns:
            allowed = set(schema.column_names())
            allowed.add(schema.primary_key)
            if schema.payload_field:
                allowed.add(schema.payload_field)
            if vector_field:
                allowed.add(vector_field)
            row = {key: value for key, value in row.items() if key in allowed}
        return row

    def _row_to_document(
        self, row: Dict[str, Any], schema: CollectionSchema
    ) -> Document:
        doc_id = row.get(schema.primary_key)
        payload: Dict[str, Any] = {}
        if schema.payload_field:
            raw = row.get(schema.payload_field)
            if isinstance(raw, memoryview):
                raw = raw.tobytes()
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode()
            if isinstance(raw, str):
                payload = json.loads(raw) if raw else {}
            elif isinstance(raw, dict):
                payload = raw
            elif raw is None:
                payload = {}
            else:
                payload = {"value": raw}
        vector: Optional[Vector] = None
        vector_field = self._vector_field(schema)
        if vector_field:
            raw_vector = row.get(vector_field)
            if raw_vector is not None:
                values = list(raw_vector) if not isinstance(raw_vector, list) else raw_vector
                vector = Vector(values=values, dimension=len(values))
        fields = {
            key: value
            for key, value in row.items()
            if key
            not in {
                schema.primary_key,
                schema.payload_field,
                vector_field,
            }
        }
        return Document(doc_id=doc_id, fields=fields, payload=payload, vector=vector)

    def _build_condition(
        self, condition, schema: CollectionSchema
    ) -> Tuple[str, List[object]]:
        field = condition.field
        operator = condition.operator.value
        value = condition.value
        source = self._resolve_source(condition.source, field, schema)
        if source == FieldSource.PAYLOAD:
            payload_field = self._payload_field(schema)
            expr = f"{self._quote_identifier(payload_field)} ->> %s"
            params: List[object] = [field]
            if operator == "EQ":
                return f"{expr} = %s", params + [str(value)]
            if operator == "NE":
                return f"{expr} != %s", params + [str(value)]
            if operator in {"GT", "GTE", "LT", "LTE"}:
                op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
                cast_expr = (
                    f"({expr})::numeric" if isinstance(value, (int, float)) else expr
                )
                return f"{cast_expr} {op_map[operator]} %s", params + [value]
            if operator in {"IN", "NOT_IN"}:
                if not isinstance(value, list):
                    raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
                placeholders = ", ".join(["%s"] * len(value))
                op = "IN" if operator == "IN" else "NOT IN"
                return f"{expr} {op} ({placeholders})", params + [
                    str(v) for v in value
                ]
            if operator == "CONTAINS":
                return f"{expr} ILIKE %s", params + [f"%{value}%"]
        column = self._quote_identifier(field)
        params = []
        if operator == "EQ":
            return f"{column} = %s", params + [value]
        if operator == "NE":
            return f"{column} != %s", params + [value]
        if operator in {"GT", "GTE", "LT", "LTE"}:
            op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
            return f"{column} {op_map[operator]} %s", params + [value]
        if operator in {"IN", "NOT_IN"}:
            if not isinstance(value, list):
                raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
            placeholders = ", ".join(["%s"] * len(value))
            op = "IN" if operator == "IN" else "NOT IN"
            return f"{column} {op} ({placeholders})", params + value
        if operator == "CONTAINS":
            return f"{column} ILIKE %s", params + [f"%{value}%"]
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _ensure_connection(self) -> None:
        if self._connection is None:
            raise RuntimeError("PostgreSQL 연결이 초기화되지 않았습니다.")

    def _ensure_schema(
        self, schema: Optional[CollectionSchema], collection: Optional[str] = None
    ) -> CollectionSchema:
        if schema is not None:
            return schema
        if collection is None:
            raise ValueError("컬렉션 이름이 필요합니다.")
        return CollectionSchema.default(collection)

    def _resolve_source(
        self, source: FieldSource, field: str, schema: CollectionSchema
    ) -> FieldSource:
        if source != FieldSource.AUTO:
            return source
        if field in {schema.primary_key, schema.vector_field}:
            return FieldSource.COLUMN
        if schema.columns and field in schema.column_names():
            return FieldSource.COLUMN
        if not schema.payload_field:
            return FieldSource.COLUMN
        return FieldSource.PAYLOAD

    def _select_columns(self, schema: CollectionSchema) -> Optional[List[str]]:
        if not schema.columns:
            return None
        names = schema.column_names()
        if schema.primary_key not in names:
            names.insert(0, schema.primary_key)
        if schema.payload_field and schema.payload_field not in names:
            names.append(schema.payload_field)
        vector_field = self._vector_field(schema)
        if vector_field and vector_field not in names:
            names.append(vector_field)
        return names

    def _select_sql(self, columns: Optional[List[str]]) -> str:
        if not columns:
            return "*"
        return ", ".join(self._quote_identifier(name) for name in columns)

    def _row_to_dict(self, cursor, row: Tuple[Any, ...]) -> Dict[str, Any]:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def _payload_field(self, schema: CollectionSchema) -> str:
        if not schema.payload_field:
            raise RuntimeError("payload 필드가 정의되어 있지 않습니다.")
        return schema.payload_field

    def _vector_field(self, schema: CollectionSchema) -> Optional[str]:
        return schema.vector_field or None

    def _vector_dimension(self, schema: CollectionSchema) -> int:
        dimension = schema.resolve_vector_dimension()
        if dimension is None:
            raise ValueError("벡터 차원 정보가 필요합니다.")
        return dimension

    def _has_vector_column(self, schema: CollectionSchema) -> bool:
        if not schema.vector_field:
            return False
        if not schema.columns:
            return True
        if schema.vector_field in schema.column_names():
            return True
        return any(column.is_vector for column in schema.columns)

    def _ensure_vector_extension(self, cursor, schema: CollectionSchema) -> None:
        if self._has_vector_column(schema):
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

    def _ensure_vector_index(self, cursor, schema: CollectionSchema) -> None:
        vector_field = self._vector_field(schema)
        if not vector_field or not self._has_vector_column(schema):
            return
        index_name = f"{schema.name}_{vector_field}_vec_idx"
        table = self._quote_table(schema.name)
        vector_col = self._quote_identifier(vector_field)
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {self._quote_identifier(index_name)} "
            f"ON {table} USING ivfflat ({vector_col} vector_cosine_ops)"
        )

    def _resolve_column_type(self, schema: CollectionSchema, column) -> str:
        if column.data_type:
            return column.data_type
        if schema.payload_field and column.name == schema.payload_field:
            return "JSONB"
        if column.is_vector or column.name == schema.vector_field:
            return f"vector({self._vector_dimension(schema)})"
        return "TEXT"

    def _quote_table(self, name: str) -> str:
        return self._quote_identifier(name)

    def _quote_identifier(self, name: str) -> str:
        if not name:
            raise ValueError("식별자 이름이 비어 있습니다.")
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"허용되지 않는 식별자: {name}")
        return f'"{name}"'

    def _json_value(self, payload: Dict[str, Any]) -> object:
        if PgJson is not None:
            return PgJson(payload)
        return json.dumps(payload)
