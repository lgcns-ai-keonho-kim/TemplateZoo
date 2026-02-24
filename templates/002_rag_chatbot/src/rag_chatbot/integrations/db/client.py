"""
목적: 공통 DB 클라이언트를 제공한다.
설명: 엔진을 주입받아 CRUD 중심의 단순한 호출을 제공한다.
디자인 패턴: 파사드
참조: src/rag_chatbot/integrations/db/base/engine.py, src/rag_chatbot/integrations/db/base/query_builder.py
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Sequence

from rag_chatbot.integrations.db.base.engine import BaseDBEngine
from rag_chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
)
from rag_chatbot.integrations.db.query_builder.delete_builder import DeleteBuilder
from rag_chatbot.integrations.db.query_builder.read_builder import ReadBuilder
from rag_chatbot.integrations.db.query_builder.write_builder import WriteBuilder


class DBClient:
    """공통 DB 클라이언트."""

    def __init__(self, engine: BaseDBEngine) -> None:
        self._engine = engine
        self._schemas: Dict[str, CollectionSchema] = {}
        self._schema_lock = threading.RLock()
        self._engine_lock = threading.RLock()

    @property
    def engine(self) -> BaseDBEngine:
        """내부 엔진을 반환한다."""

        return self._engine

    def connect(self) -> None:
        """엔진 연결을 초기화한다."""

        with self._engine_lock:
            self._engine.connect()

    def close(self) -> None:
        """엔진 연결을 종료한다."""

        with self._engine_lock:
            self._engine.close()

    def register_schema(self, schema: CollectionSchema) -> None:
        """컬렉션 스키마를 등록한다."""

        with self._schema_lock:
            schema_snapshot = schema.model_copy(deep=True)
            if schema_snapshot.vector_field and not self._engine.supports_vector_search:
                raise RuntimeError("이 엔진은 벡터 필드를 지원하지 않습니다.")
            self._schemas[schema_snapshot.name] = schema_snapshot

    def get_schema(self, collection: str) -> CollectionSchema:
        """컬렉션 스키마를 조회한다."""

        with self._schema_lock:
            schema = self._schemas.get(collection)
            if schema is None:
                return CollectionSchema.default(collection)
            return schema.model_copy(deep=True)

    def create_collection(self, schema: CollectionSchema) -> None:
        """스키마 기반으로 컬렉션을 생성한다."""

        schema_snapshot = schema.model_copy(deep=True)
        self.register_schema(schema_snapshot)
        with self._engine_lock:
            self._engine.create_collection(schema_snapshot)

    def add_column(self, collection: str, column: ColumnSpec) -> None:
        """컬럼을 추가한다."""

        schema_snapshot = self.get_schema(collection)
        if column.name == schema_snapshot.primary_key:
            raise ValueError("기본 키 컬럼은 추가할 수 없습니다.")
        if schema_snapshot.vector_field and column.name == schema_snapshot.vector_field:
            raise ValueError("벡터 필드는 스키마에 이미 정의되어 있습니다.")
        with self._engine_lock:
            self._engine.add_column(collection, column, schema_snapshot)
        with self._schema_lock:
            current = self._schemas.get(collection) or CollectionSchema.default(collection)
            updated = current.model_copy(deep=True)
            if not any(item.name == column.name for item in updated.columns):
                updated.columns.append(column.model_copy(deep=True))
            self._schemas[collection] = updated

    def drop_column(self, collection: str, column_name: str) -> None:
        """컬럼을 삭제한다."""

        schema_snapshot = self.get_schema(collection)
        if column_name == schema_snapshot.primary_key:
            raise ValueError("기본 키 컬럼은 삭제할 수 없습니다.")
        with self._engine_lock:
            self._engine.drop_column(collection, column_name, schema_snapshot)
        with self._schema_lock:
            current = self._schemas.get(collection)
            if current is None:
                return
            updated = current.model_copy(deep=True)
            updated.columns = [col for col in updated.columns if col.name != column_name]
            if updated.payload_field == column_name:
                updated.payload_field = None
            if updated.vector_field == column_name:
                updated.vector_field = None
                updated.vector_dimension = None
            self._schemas[collection] = updated

    def write(self, collection: str) -> WriteBuilder:
        """쓰기 DSL 빌더를 반환한다."""

        return WriteBuilder(
            self._engine,
            collection,
            self.get_schema(collection),
            upsert_executor=self._upsert_with_schema,
        )

    def read(self, collection: str) -> ReadBuilder:
        """읽기 DSL 빌더를 반환한다."""

        return ReadBuilder(
            self._engine,
            collection,
            self.get_schema(collection),
            query_executor=self._query_with_schema,
            vector_executor=self._vector_search_with_schema,
        )

    def delete(self, collection: str) -> DeleteBuilder:
        """삭제 DSL 빌더를 반환한다."""

        return DeleteBuilder(
            self._engine,
            collection,
            self.get_schema(collection),
            query_executor=self._query_with_schema,
            delete_executor=self._delete_with_schema,
        )

    def fetch(self, collection: str, query: Optional[Query] = None) -> List[Document]:
        """Query 기반으로 문서를 조회한다."""

        if query is None:
            query = Query()
        return self._query_with_schema(collection, query)

    def upsert(self, collection: str, documents: Sequence[Document]) -> None:
        """문서를 업서트한다."""

        self._upsert_with_schema(collection, documents)

    def vector_search(self, request: VectorSearchRequest) -> VectorSearchResponse:
        """벡터 검색을 수행한다."""

        return self._vector_search_with_schema(request, schema=None)

    def _resolve_schema(
        self,
        collection: str,
        schema: Optional[CollectionSchema] = None,
    ) -> CollectionSchema:
        if schema is None:
            return self.get_schema(collection)
        return schema.model_copy(deep=True)

    def _query_with_schema(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        resolved_schema = self._resolve_schema(collection, schema)
        resolved_schema.validate_query(query)
        if self._should_serialize_read_io():
            with self._engine_lock:
                return self._engine.query(collection, query, resolved_schema)
        return self._engine.query(collection, query, resolved_schema)

    def _upsert_with_schema(
        self,
        collection: str,
        documents: Sequence[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = self._resolve_schema(collection, schema)
        docs = list(documents)
        for document in docs:
            resolved_schema.validate_document(document)
        with self._engine_lock:
            self._engine.upsert(collection, docs, resolved_schema)

    def _delete_with_schema(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = self._resolve_schema(collection, schema)
        with self._engine_lock:
            self._engine.delete(collection, doc_id, resolved_schema)

    def _vector_search_with_schema(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        resolved_schema = self._resolve_schema(request.collection, schema)
        if not resolved_schema.vector_field:
            raise ValueError("벡터 필드가 정의되어 있지 않습니다.")
        if not self._engine.supports_vector_search:
            raise RuntimeError("이 엔진은 벡터 검색을 지원하지 않습니다.")
        resolved_schema.validate_filter_expression(request.filter_expression)
        if self._should_serialize_read_io():
            with self._engine_lock:
                return self._engine.vector_search(request, resolved_schema)
        return self._engine.vector_search(request, resolved_schema)

    def _should_serialize_read_io(self) -> bool:
        engine_name = str(getattr(self._engine, "name", "")).strip().lower()
        return engine_name == "sqlite"
