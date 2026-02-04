"""
목적: MySQL 기반 DB 엔진을 제공한다.
설명: 컬렉션 스키마 기반 CRUD를 지원하며 벡터 검색은 제공하지 않는다.
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
    VectorSearchRequest,
    VectorSearchResponse,
)

try:
    import mysql.connector
except ImportError:  # pragma: no cover - 환경 의존 로딩
    mysql = None

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class MySQLEngine(BaseDBEngine):
    """MySQL 기반 엔진 구현체."""

    def __init__(
        self,
        dsn: Optional[dict] = None,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: Optional[str] = None,
        database: str = "mysql",
        logger: Optional[Logger] = None,
    ) -> None:
        if dsn is None:
            dsn = {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": database,
            }
        self._dsn = dsn
        self._logger = logger or create_default_logger("MySQLEngine")
        self._connection = None

    @property
    def name(self) -> str:
        return "mysql"

    @property
    def supports_vector_search(self) -> bool:
        return False

    def connect(self) -> None:
        if mysql is None:
            raise RuntimeError("mysql-connector-python 패키지가 설치되어 있지 않습니다.")
        if self._connection is not None:
            return
        self._connection = mysql.connector.connect(**self._dsn)
        self._logger.info("MySQL 연결이 초기화되었습니다.")

    def close(self) -> None:
        if self._connection is None:
            return
        self._connection.close()
        self._connection = None
        self._logger.info("MySQL 연결이 종료되었습니다.")

    def create_collection(self, schema: CollectionSchema) -> None:
        self._ensure_connection()
        schema = self._ensure_schema(schema)
        if schema.vector_field or any(column.is_vector for column in schema.columns):
            raise RuntimeError("MySQL은 벡터 필드를 지원하지 않습니다.")
        table = self._quote_table(schema.name)
        cursor = self._connection.cursor()
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
                    f"PRIMARY KEY ({self._quote_identifier(schema.primary_key)})"
                )
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
            )
        else:
            column_defs = [
                f"{self._quote_identifier(schema.primary_key)} VARCHAR(255) PRIMARY KEY"
            ]
            if schema.payload_field:
                column_defs.append(
                    f"{self._quote_identifier(schema.payload_field)} JSON"
                )
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
            )
        self._connection.commit()
        self._logger.info(f"MySQL 테이블 생성 완료: {schema.name}")

    def delete_collection(self, name: str) -> None:
        self._ensure_connection()
        table = self._quote_table(name)
        cursor = self._connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        self._connection.commit()
        self._logger.info(f"MySQL 테이블 삭제 완료: {name}")

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
        if column.is_vector or column.name == schema.vector_field:
            raise RuntimeError("MySQL은 벡터 필드를 지원하지 않습니다.")
        table = self._quote_table(schema.name)
        column_name = self._quote_identifier(column.name)
        data_type = self._resolve_column_type(schema, column)
        cursor = self._connection.cursor()
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column_name} {data_type}"
        )
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
        if column_name == schema.vector_field:
            raise RuntimeError("MySQL은 벡터 필드를 지원하지 않습니다.")
        table = self._quote_table(schema.name)
        cursor = self._connection.cursor()
        cursor.execute(
            f"ALTER TABLE {table} DROP COLUMN {self._quote_identifier(column_name)}"
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
        if schema.vector_field:
            raise RuntimeError("MySQL은 벡터 필드를 지원하지 않습니다.")
        table = self._quote_table(schema.name)
        cursor = self._connection.cursor()
        for document in documents:
            if document.vector is not None:
                raise RuntimeError("MySQL은 벡터 필드를 지원하지 않습니다.")
            row = self._document_to_row(document, schema)
            if not row:
                continue
            columns = list(row.keys())
            placeholders = ", ".join(["%s"] * len(columns))
            column_sql = ", ".join(self._quote_identifier(col) for col in columns)
            update_columns = [c for c in columns if c != schema.primary_key]
            update_sql = ", ".join(
                f"{self._quote_identifier(col)} = VALUES({self._quote_identifier(col)})"
                for col in update_columns
            )
            sql = (
                f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {update_sql}"
                if update_sql
                else f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})"
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
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(
            f"SELECT {select_sql} FROM {table} WHERE {pk} = %s",
            (doc_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_document(row, schema)

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
        cursor = self._connection.cursor()
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
        sql = f"SELECT {select_sql} FROM {table}"
        params: List[object] = []
        if query.filter_expression and query.filter_expression.conditions:
            clauses = []
            for condition in query.filter_expression.conditions:
                clause, clause_params = self._build_condition(condition, schema)
                clauses.append(clause)
                params.extend(clause_params)
            joiner = " OR " if query.filter_expression.logic == "OR" else " AND "
            sql += " WHERE " + joiner.join(clauses)
        if query.sort:
            order_by_parts = []
            for sort_field in query.sort:
                order = "ASC" if sort_field.order == SortOrder.ASC else "DESC"
                source = self._resolve_source(sort_field.source, sort_field.field, schema)
                if source == FieldSource.PAYLOAD:
                    payload_field = self._payload_field(schema)
                    order_by_parts.append(
                        f"JSON_EXTRACT({self._quote_identifier(payload_field)}, '$.{sort_field.field}') {order}"
                    )
                else:
                    order_by_parts.append(
                        f"{self._quote_identifier(sort_field.field)} {order}"
                    )
            sql += " ORDER BY " + ", ".join(order_by_parts)
        if query.pagination:
            sql += " LIMIT %s OFFSET %s"
            params.extend([query.pagination.limit, query.pagination.offset])
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [self._row_to_document(row, schema) for row in rows]

    def vector_search(
        self, request: VectorSearchRequest, schema: Optional[CollectionSchema] = None
    ) -> VectorSearchResponse:
        raise RuntimeError("MySQL은 벡터 검색을 지원하지 않습니다.")

    def _document_to_row(
        self, document: Document, schema: CollectionSchema
    ) -> Dict[str, Any]:
        row: Dict[str, Any] = {schema.primary_key: document.doc_id}
        if schema.payload_field:
            row[schema.payload_field] = json.dumps(document.payload)
        for key, value in document.fields.items():
            row[key] = value
        if schema.columns:
            allowed = set(schema.column_names())
            allowed.add(schema.primary_key)
            if schema.payload_field:
                allowed.add(schema.payload_field)
            row = {key: value for key, value in row.items() if key in allowed}
        return row

    def _row_to_document(
        self, row: Dict[str, Any], schema: CollectionSchema
    ) -> Document:
        doc_id = row.get(schema.primary_key)
        payload: Dict[str, Any] = {}
        if schema.payload_field:
            raw = row.get(schema.payload_field)
            if isinstance(raw, str):
                payload = json.loads(raw) if raw else {}
            elif isinstance(raw, dict):
                payload = raw
            elif raw is None:
                payload = {}
            else:
                payload = {"value": raw}
        fields = {
            key: value
            for key, value in row.items()
            if key
            not in {
                schema.primary_key,
                schema.payload_field,
            }
        }
        return Document(doc_id=doc_id, fields=fields, payload=payload, vector=None)

    def _build_condition(
        self, condition, schema: CollectionSchema
    ) -> Tuple[str, List[object]]:
        field = condition.field
        operator = condition.operator.value
        value = condition.value
        source = self._resolve_source(condition.source, field, schema)
        if source == FieldSource.PAYLOAD:
            payload_field = self._payload_field(schema)
            expr = f"JSON_EXTRACT({self._quote_identifier(payload_field)}, %s)"
            field_path = f"$.{field}"
            params: List[object] = [field_path]
            if operator == "EQ":
                return f"{expr} = %s", params + [value]
            if operator == "NE":
                return f"{expr} != %s", params + [value]
            if operator in {"GT", "GTE", "LT", "LTE"}:
                op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
                cast_expr = (
                    f"CAST(JSON_UNQUOTE({expr}) AS DECIMAL(65, 30))"
                    if isinstance(value, (int, float))
                    else f"JSON_UNQUOTE({expr})"
                )
                return f"{cast_expr} {op_map[operator]} %s", params + [value]
            if operator in {"IN", "NOT_IN"}:
                if not isinstance(value, list):
                    raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
                placeholders = ", ".join(["%s"] * len(value))
                op = "IN" if operator == "IN" else "NOT IN"
                return f"{expr} {op} ({placeholders})", params + value
            if operator == "CONTAINS":
                return f"JSON_UNQUOTE({expr}) LIKE %s", params + [f"%{value}%"]
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
            return f"{column} LIKE %s", params + [f"%{value}%"]
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _ensure_connection(self) -> None:
        if self._connection is None:
            raise RuntimeError("MySQL 연결이 초기화되지 않았습니다.")

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
        if field == schema.primary_key:
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
        return names

    def _select_sql(self, columns: Optional[List[str]]) -> str:
        if not columns:
            return "*"
        return ", ".join(self._quote_identifier(name) for name in columns)

    def _payload_field(self, schema: CollectionSchema) -> str:
        if not schema.payload_field:
            raise RuntimeError("payload 필드가 정의되어 있지 않습니다.")
        return schema.payload_field

    def _resolve_column_type(self, schema: CollectionSchema, column) -> str:
        if column.data_type:
            return column.data_type
        if schema.payload_field and column.name == schema.payload_field:
            return "JSON"
        return "TEXT"

    def _quote_table(self, name: str) -> str:
        return self._quote_identifier(name)

    def _quote_identifier(self, name: str) -> str:
        if not name:
            raise ValueError("식별자 이름이 비어 있습니다.")
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"허용되지 않는 식별자: {name}")
        return f"`{name}`"
