"""
목적: SQLite 기반 DB 엔진을 제공한다.
설명: 컬렉션 스키마 기반 CRUD와 sqlite-vec 벡터 검색을 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/integrations/db/base/engine.py
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Dict, List, Optional

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
    import sqlite_vec
except ImportError:  # pragma: no cover - 환경 의존 로딩
    sqlite_vec = None

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SqliteVectorEngine(BaseDBEngine):
    """sqlite-vec 기반 SQLite 엔진 구현체."""

    def __init__(
        self,
        database_path: str = "data/db/playground.sqlite",
        logger: Optional[Logger] = None,
        enable_vector: bool = True,
    ) -> None:
        self._database_path = database_path
        self._logger = logger or create_default_logger("SqliteVectorEngine")
        self._enable_vector = enable_vector
        self._connection: Optional[sqlite3.Connection] = None
        self._supports_vector_search = enable_vector
        self._vector_tables: Dict[str, str] = {}

    @property
    def name(self) -> str:
        return "sqlite"

    @property
    def supports_vector_search(self) -> bool:
        return self._supports_vector_search

    def connect(self) -> None:
        if self._connection is not None:
            return
        self._connection = sqlite3.connect(self._database_path)
        self._connection.row_factory = sqlite3.Row
        if self._enable_vector:
            self._load_sqlite_vec()
        self._logger.info("SQLite 연결이 초기화되었습니다.")

    def close(self) -> None:
        if self._connection is None:
            return
        self._connection.close()
        self._connection = None
        self._logger.info("SQLite 연결이 종료되었습니다.")

    def create_collection(self, schema: CollectionSchema) -> None:
        self._ensure_connection()
        schema = self._ensure_schema(schema)
        table = self._quote_table(schema.name)
        cursor = self._connection.cursor()
        if schema.columns:
            column_defs = []
            for column in schema.columns:
                col_name = self._quote_identifier(column.name)
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
            column_defs = [f"{self._quote_identifier(schema.primary_key)} TEXT PRIMARY KEY"]
            if schema.payload_field:
                column_defs.append(
                    f"{self._quote_identifier(schema.payload_field)} TEXT"
                )
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(column_defs)})"
            )
        vector_field = self._vector_field(schema)
        if vector_field:
            if not self._enable_vector:
                raise RuntimeError("벡터 저장이 비활성화되었습니다.")
            vector_dim = self._vector_dimension(schema)
            vector_table = self._vector_table(schema)
            cursor.execute(
                " ".join(
                    [
                        f"CREATE VIRTUAL TABLE IF NOT EXISTS {self._quote_identifier(vector_table)}",
                        "USING vec0(",
                        f"{self._quote_identifier(schema.primary_key)} TEXT PRIMARY KEY,",
                        f"{self._quote_identifier(vector_field)} float[{vector_dim}]",
                        ")",
                    ]
                )
            )
            self._vector_tables[schema.name] = vector_table
        self._connection.commit()

    def delete_collection(self, name: str) -> None:
        self._ensure_connection()
        table = self._quote_table(name)
        cursor = self._connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        if self._enable_vector:
            vector_table = self._vector_tables.pop(name, None)
            if vector_table:
                cursor.execute(
                    f"DROP TABLE IF EXISTS {self._quote_identifier(vector_table)}"
                )
            cursor.execute(
                f"DROP TABLE IF EXISTS {self._quote_identifier(f'vec_{name}')}"
            )
        self._connection.commit()

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
            if not self._enable_vector:
                raise RuntimeError("벡터 저장이 비활성화되었습니다.")
            vector_dim = self._vector_dimension(schema)
            vector_table = self._vector_table(schema)
            cursor = self._connection.cursor()
            cursor.execute(
                " ".join(
                    [
                        f"CREATE VIRTUAL TABLE IF NOT EXISTS {self._quote_identifier(vector_table)}",
                        "USING vec0(",
                        f"{self._quote_identifier(schema.primary_key)} TEXT PRIMARY KEY,",
                        f"{self._quote_identifier(column.name)} float[{vector_dim}]",
                        ")",
                    ]
                )
            )
            self._vector_tables[schema.name] = vector_table
            self._connection.commit()
            return
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
            vector_table = self._vector_table(schema)
            cursor = self._connection.cursor()
            cursor.execute(
                f"DROP TABLE IF EXISTS {self._quote_identifier(vector_table)}"
            )
            self._vector_tables.pop(schema.name, None)
            self._connection.commit()
            return
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
        table = self._quote_table(schema.name)
        cursor = self._connection.cursor()
        for document in documents:
            row = self._document_to_row(document, schema)
            if not row:
                continue
            columns = list(row.keys())
            placeholders = ", ".join(["?"] * len(columns))
            column_sql = ", ".join(self._quote_identifier(col) for col in columns)
            cursor.execute(
                f"INSERT OR REPLACE INTO {table} ({column_sql}) VALUES ({placeholders})",
                list(row.values()),
            )
            vector_field = self._vector_field(schema)
            if vector_field and document.vector:
                if not self._enable_vector:
                    raise RuntimeError("벡터 저장이 비활성화되었습니다.")
                vector = document.vector
                if vector.dimension is None:
                    vector = Vector(values=vector.values, dimension=len(vector.values))
                cursor.execute(
                    " ".join(
                        [
                            f"INSERT OR REPLACE INTO {self._quote_identifier(self._vector_table(schema))}",
                            f"({self._quote_identifier(schema.primary_key)}, {self._quote_identifier(vector_field)})",
                            "VALUES (?, ?)",
                        ]
                    ),
                    (document.doc_id, vector.values),
                )
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
        cursor = self._connection.cursor()
        row = cursor.execute(
            f"SELECT {select_sql} FROM {table} WHERE {pk} = ?",
            (doc_id,),
        ).fetchone()
        if row is None:
            return None
        row_dict = dict(row)
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
        cursor = self._connection.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE {pk} = ?", (doc_id,))
        if self._enable_vector and self._vector_field(schema):
            cursor.execute(
                f"DELETE FROM {self._quote_identifier(self._vector_table(schema))} "
                f"WHERE {self._quote_identifier(schema.primary_key)} = ?",
                (doc_id,),
            )
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
                order = sort_field.order.value
                source = self._resolve_source(sort_field.source, sort_field.field, schema)
                if source == FieldSource.PAYLOAD:
                    payload_field = self._payload_field(schema)
                    order_by_parts.append(
                        f"json_extract({self._quote_identifier(payload_field)}, '$.{sort_field.field}') {order}"
                    )
                else:
                    order_by_parts.append(
                        f"{self._quote_identifier(sort_field.field)} {order}"
                    )
            sql += " ORDER BY " + ", ".join(order_by_parts)
        if query.pagination:
            sql += " LIMIT ? OFFSET ?"
            params.extend([query.pagination.limit, query.pagination.offset])
        cursor = self._connection.cursor()
        rows = cursor.execute(sql, params).fetchall()
        return [self._row_to_document(dict(row), schema) for row in rows]

    def vector_search(
        self, request: VectorSearchRequest, schema: Optional[CollectionSchema] = None
    ) -> VectorSearchResponse:
        self._ensure_connection()
        schema = self._ensure_schema(schema, request.collection)
        vector_field = self._vector_field(schema)
        if not vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        if not self._enable_vector:
            raise RuntimeError("벡터 검색이 비활성화되었습니다.")
        cursor = self._connection.cursor()
        rows = cursor.execute(
            " ".join(
                [
                    f"SELECT {self._quote_identifier(schema.primary_key)}, distance FROM {self._quote_identifier(self._vector_table(schema))}",
                    f"WHERE {self._quote_identifier(vector_field)} MATCH ?",
                    "AND k = ?",
                ]
            ),
            (request.vector.values, request.top_k),
        ).fetchall()
        results: List[VectorSearchResult] = []
        for row in rows:
            doc_id = row[0]
            document = self.get(request.collection, doc_id, schema)
            if document is None:
                continue
            if request.filter_expression and not self._match_filter(
                document, request.filter_expression, schema
            ):
                continue
            if not request.include_vectors:
                document.vector = None
            results.append(
                VectorSearchResult(document=document, score=float(row[1]))
            )
        return VectorSearchResponse(results=results, total=len(results))

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
        vector = self._load_vector(schema, doc_id)
        fields = {
            key: value
            for key, value in row.items()
            if key not in {schema.primary_key, schema.payload_field}
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
            expr = f"json_extract({self._quote_identifier(payload_field)}, ?)"
            field_path = f"$.{field}"
            params: List[object] = [field_path]
            if operator == "EQ":
                return f"{expr} = ?", params + [value]
            if operator == "NE":
                return f"{expr} != ?", params + [value]
            if operator in {"GT", "GTE", "LT", "LTE"}:
                op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
                cast_expr = (
                    "CAST(json_extract("
                    f"{self._quote_identifier(payload_field)}, ?) AS REAL)"
                    if isinstance(value, (int, float))
                    else expr
                )
                return f"{cast_expr} {op_map[operator]} ?", params + [value]
            if operator in {"IN", "NOT_IN"}:
                if not isinstance(value, list):
                    raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
                placeholders = ", ".join(["?"] * len(value))
                op = "IN" if operator == "IN" else "NOT IN"
                return f"{expr} {op} ({placeholders})", params + value
            if operator == "CONTAINS":
                return f"{expr} LIKE ?", params + [f"%{value}%"]
        column = self._quote_identifier(field)
        params = []
        if operator == "EQ":
            return f"{column} = ?", params + [value]
        if operator == "NE":
            return f"{column} != ?", params + [value]
        if operator in {"GT", "GTE", "LT", "LTE"}:
            op_map = {"GT": ">", "GTE": ">=", "LT": "<", "LTE": "<="}
            return f"{column} {op_map[operator]} ?", params + [value]
        if operator in {"IN", "NOT_IN"}:
            if not isinstance(value, list):
                raise ValueError("IN/NOT_IN은 리스트 값이 필요합니다.")
            placeholders = ", ".join(["?"] * len(value))
            op = "IN" if operator == "IN" else "NOT IN"
            return f"{column} {op} ({placeholders})", params + value
        if operator == "CONTAINS":
            return f"{column} LIKE ?", params + [f"%{value}%"]
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _match_filter(self, document: Document, filter_expression, schema: CollectionSchema) -> bool:
        logic = filter_expression.logic
        results = [
            self._evaluate_condition(document, condition, schema)
            for condition in filter_expression.conditions
        ]
        if logic == "OR":
            return any(results)
        return all(results)

    def _evaluate_condition(self, document: Document, condition, schema: CollectionSchema) -> bool:
        source = self._resolve_source(condition.source, condition.field, schema)
        if source == FieldSource.PAYLOAD:
            value = document.payload.get(condition.field)
        else:
            value = document.fields.get(condition.field)
        operator = condition.operator.value
        target = condition.value
        if operator == "EQ":
            return value == target
        if operator == "NE":
            return value != target
        if operator == "GT":
            return self._compare(value, target, lambda a, b: a > b)
        if operator == "GTE":
            return self._compare(value, target, lambda a, b: a >= b)
        if operator == "LT":
            return self._compare(value, target, lambda a, b: a < b)
        if operator == "LTE":
            return self._compare(value, target, lambda a, b: a <= b)
        if operator == "IN":
            return value in target if isinstance(target, list) else False
        if operator == "NOT_IN":
            return value not in target if isinstance(target, list) else False
        if operator == "CONTAINS":
            if isinstance(value, list):
                return target in value
            if isinstance(value, str):
                return str(target) in value
            return False
        return False

    def _compare(self, left, right, func) -> bool:
        if left is None:
            return False
        try:
            return func(left, right)
        except TypeError:
            return False

    def _load_sqlite_vec(self) -> None:
        if sqlite_vec is None:
            self._supports_vector_search = False
            raise RuntimeError("sqlite-vec 패키지가 설치되어 있지 않습니다.")
        self._connection.enable_load_extension(True)
        sqlite_vec.load(self._connection)
        self._connection.enable_load_extension(False)

    def _ensure_connection(self) -> None:
        if self._connection is None:
            raise RuntimeError("SQLite 연결이 초기화되지 않았습니다.")

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
        return names

    def _select_sql(self, columns: Optional[List[str]]) -> str:
        if not columns:
            return "*"
        return ", ".join(self._quote_identifier(name) for name in columns)

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

    def _vector_table(self, schema: CollectionSchema) -> str:
        return schema.vector_table or f"vec_{schema.name}"

    def _load_vector(self, schema: CollectionSchema, doc_id: object) -> Optional[Vector]:
        vector_field = self._vector_field(schema)
        if not vector_field or not self._enable_vector:
            return None
        cursor = self._connection.cursor()
        row = cursor.execute(
            " ".join(
                [
                    f"SELECT {self._quote_identifier(vector_field)} FROM {self._quote_identifier(self._vector_table(schema))}",
                    f"WHERE {self._quote_identifier(schema.primary_key)} = ?",
                ]
            ),
            (doc_id,),
        ).fetchone()
        if row is None:
            return None
        embedding = row[0]
        if sqlite_vec and isinstance(embedding, (bytes, bytearray)):
            try:
                embedding = sqlite_vec.deserialize(embedding)
            except Exception:  # noqa: BLE001 - 환경 차이로 인한 실패 허용
                return None
        if isinstance(embedding, list):
            return Vector(values=embedding, dimension=len(embedding))
        return None

    def _resolve_column_type(self, schema: CollectionSchema, column) -> str:
        if column.data_type:
            return column.data_type
        if schema.payload_field and column.name == schema.payload_field:
            return "TEXT"
        if column.is_vector or column.name == schema.vector_field:
            return "BLOB"
        return "TEXT"

    def _quote_table(self, name: str) -> str:
        return self._quote_identifier(name)

    def _quote_identifier(self, name: str) -> str:
        if not name:
            raise ValueError("식별자 이름이 비어 있습니다.")
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"허용되지 않는 식별자: {name}")
        return f'"{name}"'
