"""
목적: DB 컬렉션 스키마 모델을 제공한다.
설명: 컬럼/페이로드/벡터 정책과 입력 검증 로직을 포함한 스키마 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/tool_proxy_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from tool_proxy_agent.integrations.db.base._column_spec import ColumnSpec
from tool_proxy_agent.integrations.db.base._field_source import FieldSource

if TYPE_CHECKING:
    from tool_proxy_agent.integrations.db.base._document import Document
    from tool_proxy_agent.integrations.db.base._filter_expression import (
        FilterExpression,
    )
    from tool_proxy_agent.integrations.db.base._query import Query


class CollectionSchema(BaseModel):
    """컬렉션(테이블) 스키마 정보를 표현한다."""

    name: str
    primary_key: str = Field(default="doc_id")
    payload_field: Optional[str] = Field(default="payload")
    vector_field: Optional[str] = Field(default=None)
    vector_table: Optional[str] = None
    vector_dimension: Optional[int] = None
    columns: List[ColumnSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def has_payload(self) -> bool:
        """페이로드 필드 존재 여부를 반환한다."""

        return bool(self.payload_field)

    def has_vector(self) -> bool:
        """벡터 필드 존재 여부를 반환한다."""

        return bool(self.vector_field)

    def column_names(self) -> List[str]:
        """등록된 컬럼 이름 목록을 반환한다."""

        return [column.name for column in self.columns]

    def resolve_vector_dimension(self) -> Optional[int]:
        """벡터 차원 정보를 반환한다."""

        if self.vector_dimension is not None:
            return self.vector_dimension
        for column in self.columns:
            if column.is_vector and column.dimension is not None:
                return column.dimension
        return None

    def resolve_source(self, field: str, source: FieldSource) -> FieldSource:
        """필드 출처를 확정한다."""

        if source != FieldSource.AUTO:
            return source
        if field == self.primary_key or field == self.vector_field:
            return FieldSource.COLUMN
        if self.columns and field in self.column_names():
            return FieldSource.COLUMN
        if not self.payload_field:
            return FieldSource.COLUMN
        return FieldSource.PAYLOAD

    def column_set(self) -> Set[str]:
        """컬럼으로 취급할 수 있는 이름 집합을 반환한다."""

        names: Set[str] = {self.primary_key}
        names.update(self.column_names())
        if self.payload_field:
            names.add(self.payload_field)
        if self.vector_field:
            names.add(self.vector_field)
        for column in self.columns:
            if column.is_vector:
                names.add(column.name)
        return names

    def validate_document(self, document: "Document") -> None:
        """문서 입력을 스키마 기준으로 검증한다."""

        if not self.payload_field and document.payload:
            raise ValueError(
                "payload 필드가 정의되지 않아 payload를 저장할 수 없습니다."
            )
        if not self.columns and document.fields:
            raise ValueError("컬럼 스키마가 없어 fields를 저장할 수 없습니다.")
        if self.columns:
            allowed = self.column_set()
            disallowed = [key for key in document.fields.keys() if key not in allowed]
            if disallowed:
                raise ValueError(f"허용되지 않는 컬럼: {', '.join(disallowed)}")
        if not self.vector_field and document.vector is not None:
            raise ValueError("벡터 필드가 정의되지 않아 vector를 저장할 수 없습니다.")

    def validate_filter_expression(
        self, filter_expression: Optional["FilterExpression"]
    ) -> None:
        """필터 표현식을 스키마 기준으로 검증한다."""

        if not filter_expression or not filter_expression.conditions:
            return
        for condition in filter_expression.conditions:
            source = self.resolve_source(condition.field, condition.source)
            if source == FieldSource.PAYLOAD and not self.payload_field:
                raise ValueError(
                    "payload 필드가 정의되지 않아 payload 조건을 사용할 수 없습니다."
                )
            if (
                source == FieldSource.COLUMN
                and condition.field not in self.column_set()
            ):
                raise ValueError(
                    f"존재하지 않는 컬럼을 조회할 수 없습니다: {condition.field}"
                )

    def validate_query(self, query: "Query") -> None:
        """쿼리 입력을 스키마 기준으로 검증한다."""

        self.validate_filter_expression(query.filter_expression)
        if not query.sort:
            return
        for sort_field in query.sort:
            source = self.resolve_source(sort_field.field, sort_field.source)
            if source == FieldSource.PAYLOAD and not self.payload_field:
                raise ValueError(
                    "payload 필드가 정의되지 않아 payload 정렬을 사용할 수 없습니다."
                )
            if (
                source == FieldSource.COLUMN
                and sort_field.field not in self.column_set()
            ):
                raise ValueError(
                    f"존재하지 않는 컬럼을 정렬에 사용할 수 없습니다: {sort_field.field}"
                )

    @classmethod
    def default(cls, name: str) -> "CollectionSchema":
        """기본 스키마를 생성한다."""

        return cls(name=name)
