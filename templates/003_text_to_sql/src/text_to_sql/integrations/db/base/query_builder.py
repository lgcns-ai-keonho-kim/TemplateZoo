"""
목적: 공통 DSL 기반 QueryBuilder를 제공한다.
설명: 체이닝 방식으로 Filter/Sort/Pagination을 구성해 Query 모델을 생성한다.
디자인 패턴: 빌더 패턴
참조: src/text_to_sql/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import List, Optional

from text_to_sql.integrations.db.base.models import (
    AggregateField,
    AggregateFunction,
    AggregateQuery,
    FieldSource,
    FilterCondition,
    FilterExpression,
    FilterOperator,
    GroupByField,
    Pagination,
    Query,
    SortField,
    SortOrder,
    Vector,
    VectorSearchRequest,
)


class QueryBuilder:
    """쿼리 DSL 빌더 클래스."""

    def __init__(self) -> None:
        self._conditions: List[FilterCondition] = []
        self._sort_fields: List[SortField] = []
        self._pagination: Optional[Pagination] = None
        self._logic: str = "AND"
        self._pending_field: Optional[str] = None
        self._pending_field_source: FieldSource = FieldSource.AUTO
        self._pending_sort_field: Optional[str] = None
        self._pending_sort_source: FieldSource = FieldSource.AUTO
        self._vector_values: Optional[List[float]] = None
        self._top_k: int = 10
        self._include_vectors: bool = False

    def where(
        self, field: str, source: FieldSource = FieldSource.AUTO
    ) -> "QueryBuilder":
        """필터 대상 필드를 지정한다."""

        self._pending_field = field
        self._pending_field_source = source
        return self

    def where_column(self, field: str) -> "QueryBuilder":
        """컬럼 기반 필터 대상을 지정한다."""

        return self.where(field, FieldSource.COLUMN)

    def where_payload(self, field: str) -> "QueryBuilder":
        """payload 기반 필터 대상을 지정한다."""

        return self.where(field, FieldSource.PAYLOAD)

    def and_(self) -> "QueryBuilder":
        """조건 결합을 AND로 설정한다."""

        self._logic = "AND"
        return self

    def or_(self) -> "QueryBuilder":
        """조건 결합을 OR로 설정한다."""

        self._logic = "OR"
        return self

    def eq(self, value: object) -> "QueryBuilder":
        """동등 조건을 추가한다."""

        return self._add_condition(FilterOperator.EQ, value)

    def ne(self, value: object) -> "QueryBuilder":
        """불일치 조건을 추가한다."""

        return self._add_condition(FilterOperator.NE, value)

    def gt(self, value: object) -> "QueryBuilder":
        """초과 조건을 추가한다."""

        return self._add_condition(FilterOperator.GT, value)

    def gte(self, value: object) -> "QueryBuilder":
        """이상 조건을 추가한다."""

        return self._add_condition(FilterOperator.GTE, value)

    def lt(self, value: object) -> "QueryBuilder":
        """미만 조건을 추가한다."""

        return self._add_condition(FilterOperator.LT, value)

    def lte(self, value: object) -> "QueryBuilder":
        """이하 조건을 추가한다."""

        return self._add_condition(FilterOperator.LTE, value)

    def in_(self, values: List[object]) -> "QueryBuilder":
        """포함 조건을 추가한다."""

        return self._add_condition(FilterOperator.IN, values)

    def not_in(self, values: List[object]) -> "QueryBuilder":
        """미포함 조건을 추가한다."""

        return self._add_condition(FilterOperator.NOT_IN, values)

    def contains(self, value: object) -> "QueryBuilder":
        """포함(문자열/배열) 조건을 추가한다."""

        return self._add_condition(FilterOperator.CONTAINS, value)

    def order_by(
        self, field: str, source: FieldSource = FieldSource.AUTO
    ) -> "QueryBuilder":
        """정렬 필드를 지정한다."""

        self._pending_sort_field = field
        self._pending_sort_source = source
        return self

    def order_by_column(self, field: str) -> "QueryBuilder":
        """컬럼 기반 정렬 필드를 지정한다."""

        return self.order_by(field, FieldSource.COLUMN)

    def order_by_payload(self, field: str) -> "QueryBuilder":
        """payload 기반 정렬 필드를 지정한다."""

        return self.order_by(field, FieldSource.PAYLOAD)

    def asc(self) -> "QueryBuilder":
        """오름차순 정렬을 추가한다."""

        return self._add_sort(SortOrder.ASC)

    def desc(self) -> "QueryBuilder":
        """내림차순 정렬을 추가한다."""

        return self._add_sort(SortOrder.DESC)

    def limit(self, value: int) -> "QueryBuilder":
        """조회 제한을 설정한다."""

        if self._pagination is None:
            self._pagination = Pagination(limit=value, offset=0)
        else:
            self._pagination = Pagination(limit=value, offset=self._pagination.offset)
        return self

    def offset(self, value: int) -> "QueryBuilder":
        """조회 오프셋을 설정한다."""

        if self._pagination is None:
            self._pagination = Pagination(limit=50, offset=value)
        else:
            self._pagination = Pagination(limit=self._pagination.limit, offset=value)
        return self

    def vector(self, values: List[float]) -> "QueryBuilder":
        """벡터 검색을 위한 벡터 값을 설정한다."""

        self._vector_values = values
        return self

    def top_k(self, value: int) -> "QueryBuilder":
        """벡터 검색 상위 결과 수를 설정한다."""

        if value <= 0:
            raise ValueError("top_k는 1 이상이어야 합니다.")
        self._top_k = value
        return self

    def include_vectors(self, enabled: bool = True) -> "QueryBuilder":
        """벡터 포함 여부를 설정한다."""

        self._include_vectors = enabled
        return self

    def build(self) -> Query:
        """Query 모델을 생성한다."""

        filter_expression = None
        if self._conditions:
            filter_expression = FilterExpression(
                conditions=list(self._conditions),
                logic=self._logic,
            )
        return Query(
            filter_expression=filter_expression,
            sort=list(self._sort_fields),
            pagination=self._pagination,
        )

    def build_vector_request(self, collection: str) -> VectorSearchRequest:
        """VectorSearchRequest 모델을 생성한다."""

        if self._vector_values is None:
            raise ValueError("vector()로 벡터 값을 먼저 지정해야 합니다.")
        vector = Vector(values=self._vector_values, dimension=len(self._vector_values))
        filter_expression = None
        if self._conditions:
            filter_expression = FilterExpression(
                conditions=list(self._conditions),
                logic=self._logic,
            )
        return VectorSearchRequest(
            collection=collection,
            vector=vector,
            top_k=self._top_k,
            filter_expression=filter_expression,
            include_vectors=self._include_vectors,
        )

    def has_vector(self) -> bool:
        """벡터 검색 설정 여부를 반환한다."""

        return self._vector_values is not None

    def reset(self) -> "QueryBuilder":
        """빌더 상태를 초기화한다."""

        self._conditions = []
        self._sort_fields = []
        self._pagination = None
        self._logic = "AND"
        self._pending_field = None
        self._pending_field_source = FieldSource.AUTO
        self._pending_sort_field = None
        self._pending_sort_source = FieldSource.AUTO
        self._vector_values = None
        self._top_k = 10
        self._include_vectors = False
        return self

    def _add_condition(self, operator: FilterOperator, value: object) -> "QueryBuilder":
        if self._pending_field is None:
            raise ValueError("where()로 필드를 먼저 지정해야 합니다.")
        self._conditions.append(
            FilterCondition(
                field=self._pending_field,
                source=self._pending_field_source,
                operator=operator,
                value=value,
            )
        )
        self._pending_field = None
        self._pending_field_source = FieldSource.AUTO
        return self

    def _add_sort(self, order: SortOrder) -> "QueryBuilder":
        if self._pending_sort_field is None:
            raise ValueError("order_by()로 필드를 먼저 지정해야 합니다.")
        self._sort_fields.append(
            SortField(
                field=self._pending_sort_field,
                source=self._pending_sort_source,
                order=order,
            )
        )
        self._pending_sort_field = None
        self._pending_sort_source = FieldSource.AUTO
        return self


class AggregateQueryBuilder:
    """집계 조회 DSL 빌더 클래스."""

    def __init__(self) -> None:
        self._query_builder = QueryBuilder()
        self._aggregates: List[AggregateField] = []
        self._group_by: List[GroupByField] = []

    def where(
        self,
        field: str,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        self._query_builder.where(field, source)
        return self

    def where_column(self, field: str) -> "AggregateQueryBuilder":
        self._query_builder.where_column(field)
        return self

    def where_payload(self, field: str) -> "AggregateQueryBuilder":
        self._query_builder.where_payload(field)
        return self

    def and_(self) -> "AggregateQueryBuilder":
        self._query_builder.and_()
        return self

    def or_(self) -> "AggregateQueryBuilder":
        self._query_builder.or_()
        return self

    def eq(self, value: object) -> "AggregateQueryBuilder":
        self._query_builder.eq(value)
        return self

    def ne(self, value: object) -> "AggregateQueryBuilder":
        self._query_builder.ne(value)
        return self

    def gt(self, value: object) -> "AggregateQueryBuilder":
        self._query_builder.gt(value)
        return self

    def gte(self, value: object) -> "AggregateQueryBuilder":
        self._query_builder.gte(value)
        return self

    def lt(self, value: object) -> "AggregateQueryBuilder":
        self._query_builder.lt(value)
        return self

    def lte(self, value: object) -> "AggregateQueryBuilder":
        self._query_builder.lte(value)
        return self

    def in_(self, values: List[object]) -> "AggregateQueryBuilder":
        self._query_builder.in_(values)
        return self

    def not_in(self, values: List[object]) -> "AggregateQueryBuilder":
        self._query_builder.not_in(values)
        return self

    def contains(self, value: object) -> "AggregateQueryBuilder":
        self._query_builder.contains(value)
        return self

    def order_by(
        self,
        field: str,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        self._query_builder.order_by(field, source)
        return self

    def order_by_column(self, field: str) -> "AggregateQueryBuilder":
        self._query_builder.order_by_column(field)
        return self

    def order_by_payload(self, field: str) -> "AggregateQueryBuilder":
        self._query_builder.order_by_payload(field)
        return self

    def asc(self) -> "AggregateQueryBuilder":
        self._query_builder.asc()
        return self

    def desc(self) -> "AggregateQueryBuilder":
        self._query_builder.desc()
        return self

    def limit(self, value: int) -> "AggregateQueryBuilder":
        self._query_builder.limit(value)
        return self

    def offset(self, value: int) -> "AggregateQueryBuilder":
        self._query_builder.offset(value)
        return self

    def max(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        return self._add_aggregate(AggregateFunction.MAX, field, alias, source)

    def min(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        return self._add_aggregate(AggregateFunction.MIN, field, alias, source)

    def sum(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        return self._add_aggregate(AggregateFunction.SUM, field, alias, source)

    def avg(
        self,
        field: str,
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        return self._add_aggregate(AggregateFunction.AVG, field, alias, source)

    def count(
        self,
        field: str = "*",
        *,
        alias: Optional[str] = None,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        return self._add_aggregate(AggregateFunction.COUNT, field, alias, source)

    def group_by(
        self,
        field: str,
        source: FieldSource = FieldSource.AUTO,
    ) -> "AggregateQueryBuilder":
        normalized = str(field or "").strip()
        if not normalized:
            raise ValueError("group_by 필드는 비어 있을 수 없습니다.")
        self._group_by.append(GroupByField(field=normalized, source=source))
        return self

    def build(self) -> AggregateQuery:
        """AggregateQuery 모델을 생성한다."""

        base_query = self._query_builder.build()
        return AggregateQuery(
            filter_expression=base_query.filter_expression,
            aggregates=list(self._aggregates),
            group_by=list(self._group_by),
            sort=list(base_query.sort),
            pagination=base_query.pagination,
        )

    def reset(self) -> "AggregateQueryBuilder":
        """빌더 상태를 초기화한다."""

        self._query_builder.reset()
        self._aggregates = []
        self._group_by = []
        return self

    def _add_aggregate(
        self,
        function: AggregateFunction,
        field: str,
        alias: Optional[str],
        source: FieldSource,
    ) -> "AggregateQueryBuilder":
        normalized_field = str(field or "").strip()
        if function != AggregateFunction.COUNT and not normalized_field:
            raise ValueError("집계 대상 필드는 비어 있을 수 없습니다.")
        if function == AggregateFunction.COUNT and not normalized_field:
            normalized_field = "*"
        normalized_alias = str(alias or "").strip() or None
        self._aggregates.append(
            AggregateField(
                function=function,
                field=normalized_field,
                source=source,
                alias=normalized_alias,
            )
        )
        return self
