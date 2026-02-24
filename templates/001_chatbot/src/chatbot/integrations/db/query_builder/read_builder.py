"""
목적: 읽기 전용 DSL 빌더를 제공한다.
설명: QueryBuilder를 감싸 체이닝 후 fetch()로 조회한다.
디자인 패턴: 빌더 패턴
참조: src/chatbot/integrations/db/base/query_builder.py
"""

from __future__ import annotations

from collections.abc import Callable
from typing import List, Optional

from chatbot.integrations.db.base.engine import BaseDBEngine
from chatbot.integrations.db.base.models import (
    CollectionSchema,
    Document,
    FieldSource,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from chatbot.integrations.db.base.query_builder import QueryBuilder


class ReadBuilder:
    """읽기 DSL 빌더."""

    def __init__(
        self,
        engine: BaseDBEngine,
        collection: str,
        schema: Optional[CollectionSchema] = None,
        query_executor: Optional[
            Callable[[str, Query, Optional[CollectionSchema]], List[Document]]
        ] = None,
        vector_executor: Optional[
            Callable[
                [VectorSearchRequest, Optional[CollectionSchema]],
                VectorSearchResponse,
            ]
        ] = None,
    ) -> None:
        self._engine = engine
        self._collection = collection
        self._builder = QueryBuilder()
        self._schema = schema
        self._query_executor = query_executor
        self._vector_executor = vector_executor

    def where(self, field: str, source: FieldSource = FieldSource.AUTO) -> "ReadBuilder":
        self._builder.where(field, source)
        return self

    def where_column(self, field: str) -> "ReadBuilder":
        self._builder.where_column(field)
        return self

    def where_payload(self, field: str) -> "ReadBuilder":
        self._builder.where_payload(field)
        return self

    def and_(self) -> "ReadBuilder":
        self._builder.and_()
        return self

    def or_(self) -> "ReadBuilder":
        self._builder.or_()
        return self

    def eq(self, value: object) -> "ReadBuilder":
        self._builder.eq(value)
        return self

    def ne(self, value: object) -> "ReadBuilder":
        self._builder.ne(value)
        return self

    def gt(self, value: object) -> "ReadBuilder":
        self._builder.gt(value)
        return self

    def gte(self, value: object) -> "ReadBuilder":
        self._builder.gte(value)
        return self

    def lt(self, value: object) -> "ReadBuilder":
        self._builder.lt(value)
        return self

    def lte(self, value: object) -> "ReadBuilder":
        self._builder.lte(value)
        return self

    def in_(self, values: List[object]) -> "ReadBuilder":
        self._builder.in_(values)
        return self

    def not_in(self, values: List[object]) -> "ReadBuilder":
        self._builder.not_in(values)
        return self

    def contains(self, value: object) -> "ReadBuilder":
        self._builder.contains(value)
        return self

    def order_by(
        self, field: str, source: FieldSource = FieldSource.AUTO
    ) -> "ReadBuilder":
        self._builder.order_by(field, source)
        return self

    def order_by_column(self, field: str) -> "ReadBuilder":
        self._builder.order_by_column(field)
        return self

    def order_by_payload(self, field: str) -> "ReadBuilder":
        self._builder.order_by_payload(field)
        return self

    def asc(self) -> "ReadBuilder":
        self._builder.asc()
        return self

    def desc(self) -> "ReadBuilder":
        self._builder.desc()
        return self

    def limit(self, value: int) -> "ReadBuilder":
        self._builder.limit(value)
        return self

    def offset(self, value: int) -> "ReadBuilder":
        self._builder.offset(value)
        return self

    def build(self) -> Query:
        """Query 모델을 반환한다."""

        return self._builder.build()

    def fetch(self) -> List[Document]:
        """일반 조회 결과를 반환한다."""

        if self._builder.has_vector():
            raise RuntimeError("벡터 검색은 fetch_vector()를 사용해야 합니다.")
        query = self.build()
        if self._query_executor is not None:
            return self._query_executor(self._collection, query, self._schema)
        if self._schema:
            self._schema.validate_query(query)
        return self._engine.query(self._collection, query, self._schema)

    def fetch_vector(self) -> VectorSearchResponse:
        """벡터 검색 결과를 반환한다."""

        if not self._builder.has_vector():
            raise RuntimeError("vector()로 벡터 값을 먼저 지정해야 합니다.")
        if not self._engine.supports_vector_search:
            raise RuntimeError("이 엔진은 벡터 검색을 지원하지 않습니다.")
        if self._schema and not self._schema.vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        request = self._builder.build_vector_request(self._collection)
        if self._vector_executor is not None:
            return self._vector_executor(request, self._schema)
        if self._schema:
            self._schema.validate_filter_expression(request.filter_expression)
        return self._engine.vector_search(request, self._schema)

    def fetch_with_scores(self) -> List[VectorSearchResult]:
        """벡터 검색 결과를 점수와 함께 반환한다."""

        return self.fetch_vector().results
