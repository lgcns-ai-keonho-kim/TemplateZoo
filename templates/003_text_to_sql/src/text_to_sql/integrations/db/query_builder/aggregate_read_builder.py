"""
목적: 집계 조회 전용 DSL 빌더를 제공한다.
설명: AggregateQueryBuilder를 감싸 체이닝 후 fetch()로 집계 조회를 수행한다.
디자인 패턴: 빌더 패턴
참조: src/text_to_sql/integrations/db/base/query_builder.py
"""

from __future__ import annotations

from collections.abc import Callable
from typing import List, Optional

from text_to_sql.integrations.db.base.engine import BaseDBEngine
from text_to_sql.integrations.db.base.models import (
    AggregateQuery,
    CollectionSchema,
    Document,
    FieldSource,
)
from text_to_sql.integrations.db.base.query_builder import AggregateQueryBuilder


class AggregateReadBuilder:
    """집계 조회 DSL 빌더."""

    def __init__(
        self,
        engine: BaseDBEngine,
        collection: str,
        schema: Optional[CollectionSchema] = None,
        aggregate_executor: Optional[
            Callable[[str, AggregateQuery, Optional[CollectionSchema]], List[Document]]
        ] = None,
    ) -> None:
        self._engine = engine
        self._collection = collection
        self._schema = schema
        self._aggregate_executor = aggregate_executor
        self._builder = AggregateQueryBuilder()

    def where(
        self,
        field: str,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.where(field, source)
        return self

    def where_column(self, field: str) -> "AggregateReadBuilder":
        self._builder.where_column(field)
        return self

    def where_payload(self, field: str) -> "AggregateReadBuilder":
        self._builder.where_payload(field)
        return self

    def and_(self) -> "AggregateReadBuilder":
        self._builder.and_()
        return self

    def or_(self) -> "AggregateReadBuilder":
        self._builder.or_()
        return self

    def eq(self, value: object) -> "AggregateReadBuilder":
        self._builder.eq(value)
        return self

    def ne(self, value: object) -> "AggregateReadBuilder":
        self._builder.ne(value)
        return self

    def gt(self, value: object) -> "AggregateReadBuilder":
        self._builder.gt(value)
        return self

    def gte(self, value: object) -> "AggregateReadBuilder":
        self._builder.gte(value)
        return self

    def lt(self, value: object) -> "AggregateReadBuilder":
        self._builder.lt(value)
        return self

    def lte(self, value: object) -> "AggregateReadBuilder":
        self._builder.lte(value)
        return self

    def in_(self, values: List[object]) -> "AggregateReadBuilder":
        self._builder.in_(values)
        return self

    def not_in(self, values: List[object]) -> "AggregateReadBuilder":
        self._builder.not_in(values)
        return self

    def contains(self, value: object) -> "AggregateReadBuilder":
        self._builder.contains(value)
        return self

    def order_by(
        self,
        field: str,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.order_by(field, source)
        return self

    def order_by_column(self, field: str) -> "AggregateReadBuilder":
        self._builder.order_by_column(field)
        return self

    def order_by_payload(self, field: str) -> "AggregateReadBuilder":
        self._builder.order_by_payload(field)
        return self

    def asc(self) -> "AggregateReadBuilder":
        self._builder.asc()
        return self

    def desc(self) -> "AggregateReadBuilder":
        self._builder.desc()
        return self

    def limit(self, value: int) -> "AggregateReadBuilder":
        self._builder.limit(value)
        return self

    def offset(self, value: int) -> "AggregateReadBuilder":
        self._builder.offset(value)
        return self

    def max(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.max(field, alias=alias, source=source)
        return self

    def min(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.min(field, alias=alias, source=source)
        return self

    def sum(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.sum(field, alias=alias, source=source)
        return self

    def avg(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.avg(field, alias=alias, source=source)
        return self

    def count(
        self,
        field: str = "*",
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.count(field=field, alias=alias, source=source)
        return self

    def group_by(
        self,
        field: str,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateReadBuilder":
        self._builder.group_by(field, source)
        return self

    def build(self) -> AggregateQuery:
        """AggregateQuery 모델을 반환한다."""

        return self._builder.build()

    def fetch(self) -> List[Document]:
        """집계 조회 결과를 반환한다."""

        query = self.build()
        if self._aggregate_executor is not None:
            return self._aggregate_executor(self._collection, query, self._schema)
        if self._schema:
            self._schema.validate_aggregate_query(query)
        return self._engine.aggregate_query(self._collection, query, self._schema)
