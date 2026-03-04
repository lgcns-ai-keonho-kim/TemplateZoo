"""
목적: LanceDB 기반 DB 엔진을 제공한다.
설명: 컬렉션 스키마 기반 CRUD와 벡터 검색을 처리한다.
디자인 패턴: 어댑터 패턴
참조: src/chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

from typing import Any, List, Optional

from chatbot.shared.logging import Logger, create_default_logger
from chatbot.integrations.db.base.engine import BaseDBEngine
from chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from chatbot.integrations.db.engines.lancedb.document_mapper import (
    LanceDocumentMapper,
)
from chatbot.integrations.db.engines.lancedb.filter_engine import (
    LanceFilterEngine,
)
from chatbot.integrations.db.engines.lancedb.schema_adapter import (
    LanceSchemaAdapter,
)
from chatbot.integrations.db.engines.sql_common import ensure_schema, vector_field

lancedb: Any | None
try:
    import lancedb as _lancedb
except ImportError:  # pragma: no cover - 환경 의존 로딩
    lancedb = None
else:  # pragma: no cover - 환경 의존 로딩
    lancedb = _lancedb


class LanceDBEngine(BaseDBEngine):
    """LanceDB 기반 엔진 구현체."""

    def __init__(
        self,
        uri: str = "data/db/vector",
        logger: Optional[Logger] = None,
    ) -> None:
        self._uri = uri
        self._logger = logger or create_default_logger("LanceDBEngine")
        self._db: Any | None = None
        self._document_mapper = LanceDocumentMapper()
        self._schema_adapter = LanceSchemaAdapter()
        self._filter_engine = LanceFilterEngine()

    @property
    def name(self) -> str:
        return "lancedb"

    @property
    def supports_vector_search(self) -> bool:
        return True

    def connect(self) -> None:
        if self._db is not None:
            return
        if lancedb is None:
            raise RuntimeError("lancedb 패키지가 설치되어 있지 않습니다.")
        self._db = lancedb.connect(self._uri)
        self._logger.info(f"LanceDB 연결이 초기화되었습니다: uri={self._uri}")

    def close(self) -> None:
        # LanceDB 파이썬 클라이언트는 명시적 close를 제공하지 않는다.
        self._db = None

    def create_collection(self, schema: CollectionSchema) -> None:
        resolved_schema = ensure_schema(schema)
        self._ensure_connected()
        if self._has_table(resolved_schema.name):
            return
        arrow_schema = self._schema_adapter.build_arrow_schema(resolved_schema)
        self._ensure_db().create_table(resolved_schema.name, schema=arrow_schema)

    def delete_collection(self, name: str) -> None:
        self._ensure_connected()
        if not self._has_table(name):
            return
        self._ensure_db().drop_table(name)

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        if column.is_primary or column.name == resolved_schema.primary_key:
            raise ValueError("기본 키 컬럼은 추가할 수 없습니다.")
        table = self._open_table_or_raise(collection)
        if column.name in table.schema.names:
            return
        table.add_columns(self._schema_adapter.build_arrow_field(column, resolved_schema))

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        if column_name == resolved_schema.primary_key:
            raise ValueError("기본 키 컬럼은 삭제할 수 없습니다.")
        table = self._open_table_or_raise(collection)
        if column_name not in table.schema.names:
            return
        table.drop_columns([column_name])

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        table = self._ensure_table(resolved_schema)

        rows: list[dict[str, Any]] = []
        for document in documents:
            raw_row = self._document_mapper.document_to_row(document, resolved_schema)
            if not raw_row:
                continue
            rows.append(
                self._schema_adapter.normalize_row(raw_row, table.schema, resolved_schema)
            )

        if not rows:
            return

        (
            table.merge_insert(resolved_schema.primary_key)
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute(rows)
        )

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        resolved_schema = ensure_schema(schema, collection)
        table = self._open_table_or_none(collection)
        if table is None:
            return None

        where = self._filter_engine.build_eq_clause(resolved_schema.primary_key, doc_id)
        rows = table.search().where(where).limit(1).to_arrow().to_pylist()
        if not rows:
            return None
        return self._document_mapper.row_to_document(rows[0], resolved_schema)

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        table = self._open_table_or_none(collection)
        if table is None:
            return

        where = self._filter_engine.build_eq_clause(resolved_schema.primary_key, doc_id)
        table.delete(where)

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        resolved_schema = ensure_schema(schema, collection)
        table = self._open_table_or_none(collection)
        if table is None:
            return []

        where_clause = self._filter_engine.build_where_clause(
            query.filter_expression,
            resolved_schema,
        )
        builder = table.search()
        if where_clause:
            builder = builder.where(where_clause)

        needs_in_memory_filter = bool(query.filter_expression and not where_clause)
        if query.sort or needs_in_memory_filter:
            rows = builder.to_arrow().to_pylist()
        else:
            if query.pagination:
                builder = builder.offset(query.pagination.offset).limit(query.pagination.limit)
            rows = builder.to_arrow().to_pylist()

        documents = [
            self._document_mapper.row_to_document(row, resolved_schema)
            for row in rows
        ]

        if query.filter_expression and not where_clause:
            documents = [
                document
                for document in documents
                if self._filter_engine.match_filter(
                    document,
                    query.filter_expression,
                    resolved_schema,
                )
            ]
            if query.pagination and not query.sort:
                start = query.pagination.offset
                end = start + query.pagination.limit
                documents = documents[start:end]

        if query.sort:
            documents = self._filter_engine.apply_sort(documents, query, resolved_schema)
            if query.pagination:
                start = query.pagination.offset
                end = start + query.pagination.limit
                documents = documents[start:end]

        return documents

    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        resolved_schema = ensure_schema(schema, request.collection)
        target_vector_field = request.vector_field or vector_field(resolved_schema)
        if not target_vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")

        table = self._open_table_or_none(request.collection)
        if table is None:
            return VectorSearchResponse(results=[], total=0)

        where_clause = self._filter_engine.build_where_clause(
            request.filter_expression,
            resolved_schema,
        )
        builder = table.search(
            request.vector.values,
            vector_column_name=target_vector_field,
        ).metric("cosine")

        if where_clause:
            builder = builder.where(where_clause).limit(max(1, request.top_k))
        elif request.filter_expression:
            builder = builder.limit(max(1, int(table.count_rows())))
        else:
            builder = builder.limit(max(1, request.top_k))

        rows = builder.to_arrow().to_pylist()
        results: list[VectorSearchResult] = []
        for row in rows:
            document = self._document_mapper.row_to_document(
                row,
                resolved_schema,
                include_vector=request.include_vectors,
            )
            if request.filter_expression and not where_clause:
                if not self._filter_engine.match_filter(
                    document,
                    request.filter_expression,
                    resolved_schema,
                ):
                    continue
            score = self._filter_engine.distance_to_similarity(
                row.get("_distance"),
                row.get("_score"),
            )
            if not request.include_vectors:
                document.vector = None
            results.append(VectorSearchResult(document=document, score=score))

        results.sort(key=lambda item: item.score, reverse=True)
        limited_results = results[: request.top_k]
        return VectorSearchResponse(results=limited_results, total=len(limited_results))

    def _ensure_connected(self) -> None:
        if self._db is None:
            self.connect()

    def _ensure_db(self):
        self._ensure_connected()
        if self._db is None:
            raise RuntimeError("LanceDB 연결이 초기화되지 않았습니다.")
        return self._db

    def _table_names(self) -> list[str]:
        result = self._ensure_db().list_tables()
        if isinstance(result, list):
            return [str(name) for name in result]
        tables = getattr(result, "tables", None)
        if isinstance(tables, list):
            return [str(name) for name in tables]
        return []

    def _has_table(self, name: str) -> bool:
        return name in self._table_names()

    def _open_table_or_none(self, name: str):
        self._ensure_connected()
        if not self._has_table(name):
            return None
        return self._ensure_db().open_table(name)

    def _open_table_or_raise(self, name: str):
        table = self._open_table_or_none(name)
        if table is None:
            raise RuntimeError(f"컬렉션이 존재하지 않습니다: {name}")
        return table

    def _ensure_table(self, schema: CollectionSchema):
        if not self._has_table(schema.name):
            self.create_collection(schema)
        return self._open_table_or_raise(schema.name)
