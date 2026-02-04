"""
목적: 공통 DB 클라이언트를 제공한다.
설명: 엔진을 주입받아 CRUD 중심의 단순한 호출을 제공한다.
디자인 패턴: 파사드
참조: src/base_template/integrations/db/base/engine.py, src/base_template/integrations/db/base/query_builder.py
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .base.engine import BaseDBEngine
from .base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
)
from .query_builder.delete_builder import DeleteBuilder
from .query_builder.read_builder import ReadBuilder
from .query_builder.write_builder import WriteBuilder


class DBClient:
    """공통 DB 클라이언트."""

    def __init__(self, engine: BaseDBEngine) -> None:
        self._engine = engine
        self._schemas: Dict[str, CollectionSchema] = {}

    @property
    def engine(self) -> BaseDBEngine:
        """내부 엔진을 반환한다."""

        return self._engine

    def connect(self) -> None:
        """엔진 연결을 초기화한다."""

        self._engine.connect()

    def close(self) -> None:
        """엔진 연결을 종료한다."""

        self._engine.close()

    def register_schema(self, schema: CollectionSchema) -> None:
        """컬렉션 스키마를 등록한다."""

        if schema.vector_field and not self._engine.supports_vector_search:
            raise RuntimeError("이 엔진은 벡터 필드를 지원하지 않습니다.")
        self._schemas[schema.name] = schema

    def get_schema(self, collection: str) -> CollectionSchema:
        """컬렉션 스키마를 조회한다."""

        return self._schemas.get(collection) or CollectionSchema.default(collection)

    def create_collection(self, schema: CollectionSchema) -> None:
        """스키마 기반으로 컬렉션을 생성한다."""

        self.register_schema(schema)
        self._engine.create_collection(schema)

    def add_column(self, collection: str, column: ColumnSpec) -> None:
        """컬럼을 추가한다."""

        schema = self.get_schema(collection)
        if column.name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 추가할 수 없습니다.")
        if schema.vector_field and column.name == schema.vector_field:
            raise ValueError("벡터 필드는 스키마에 이미 정의되어 있습니다.")
        self._engine.add_column(collection, column, schema)
        if not any(item.name == column.name for item in schema.columns):
            schema.columns.append(column)

    def drop_column(self, collection: str, column_name: str) -> None:
        """컬럼을 삭제한다."""

        schema = self.get_schema(collection)
        if column_name == schema.primary_key:
            raise ValueError("기본 키 컬럼은 삭제할 수 없습니다.")
        self._engine.drop_column(collection, column_name, schema)
        schema.columns = [col for col in schema.columns if col.name != column_name]
        if schema.payload_field == column_name:
            schema.payload_field = None
        if schema.vector_field == column_name:
            schema.vector_field = None
            schema.vector_dimension = None

    def write(self, collection: str) -> WriteBuilder:
        """쓰기 DSL 빌더를 반환한다."""

        return WriteBuilder(self._engine, collection, self.get_schema(collection))

    def read(self, collection: str) -> ReadBuilder:
        """읽기 DSL 빌더를 반환한다."""

        return ReadBuilder(self._engine, collection, self.get_schema(collection))

    def delete(self, collection: str) -> DeleteBuilder:
        """삭제 DSL 빌더를 반환한다."""

        return DeleteBuilder(self._engine, collection, self.get_schema(collection))

    def fetch(self, collection: str, query: Optional[Query] = None) -> List[Document]:
        """Query 기반으로 문서를 조회한다."""

        if query is None:
            query = Query()
        self.get_schema(collection).validate_query(query)
        return self._engine.query(collection, query, self.get_schema(collection))

    def upsert(self, collection: str, documents: Sequence[Document]) -> None:
        """문서를 업서트한다."""

        schema = self.get_schema(collection)
        for document in documents:
            schema.validate_document(document)
        self._engine.upsert(collection, list(documents), schema)

    def vector_search(self, request: VectorSearchRequest) -> VectorSearchResponse:
        """벡터 검색을 수행한다."""

        schema = self.get_schema(request.collection)
        if not schema.vector_field:
            raise ValueError("벡터 필드가 정의되어 있지 않습니다.")
        if not self._engine.supports_vector_search:
            raise RuntimeError("이 엔진은 벡터 검색을 지원하지 않습니다.")
        schema.validate_filter_expression(request.filter_expression)
        return self._engine.vector_search(request, schema)
