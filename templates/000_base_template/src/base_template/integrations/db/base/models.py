"""
목적: DB 통합 인터페이스에서 공통으로 사용하는 모델을 정의한다.
설명: 컬렉션/문서/필터/정렬/페이지네이션/벡터 검색 모델을 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/integrations/db/base/engine.py
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class ColumnSpec(BaseModel):
    """컬럼 스펙을 표현한다."""

    name: str
    data_type: Optional[str] = None
    nullable: bool = True
    is_primary: bool = False
    is_vector: bool = False
    dimension: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


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

    def resolve_source(self, field: str, source: "FieldSource") -> "FieldSource":
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
            raise ValueError("payload 필드가 정의되지 않아 payload를 저장할 수 없습니다.")
        if not self.columns and document.fields:
            raise ValueError("컬럼 스키마가 없어 fields를 저장할 수 없습니다.")
        if self.columns:
            allowed = self.column_set()
            disallowed = [
                key
                for key in document.fields.keys()
                if key not in allowed
            ]
            if disallowed:
                raise ValueError(f"허용되지 않는 컬럼: {', '.join(disallowed)}")
        if not self.vector_field and document.vector is not None:
            raise ValueError("벡터 필드가 정의되지 않아 vector를 저장할 수 없습니다.")

    def validate_filter_expression(self, filter_expression: Optional["FilterExpression"]) -> None:
        """필터 표현식을 스키마 기준으로 검증한다."""

        if not filter_expression or not filter_expression.conditions:
            return
        for condition in filter_expression.conditions:
            source = self.resolve_source(condition.field, condition.source)
            if source == FieldSource.PAYLOAD and not self.payload_field:
                raise ValueError("payload 필드가 정의되지 않아 payload 조건을 사용할 수 없습니다.")
            if source == FieldSource.COLUMN and condition.field not in self.column_set():
                raise ValueError(f"존재하지 않는 컬럼을 조회할 수 없습니다: {condition.field}")

    def validate_query(self, query: "Query") -> None:
        """쿼리 입력을 스키마 기준으로 검증한다."""

        self.validate_filter_expression(query.filter_expression)
        if not query.sort:
            return
        for sort_field in query.sort:
            source = self.resolve_source(sort_field.field, sort_field.source)
            if source == FieldSource.PAYLOAD and not self.payload_field:
                raise ValueError("payload 필드가 정의되지 않아 payload 정렬을 사용할 수 없습니다.")
            if source == FieldSource.COLUMN and sort_field.field not in self.column_set():
                raise ValueError(f"존재하지 않는 컬럼을 정렬에 사용할 수 없습니다: {sort_field.field}")

    @classmethod
    def default(cls, name: str) -> "CollectionSchema":
        """기본 스키마를 생성한다."""

        return cls(name=name)


class Vector(BaseModel):
    """벡터 데이터를 표현한다."""

    values: List[float]
    dimension: Optional[int] = None


class Document(BaseModel):
    """문서 데이터를 표현한다."""

    doc_id: Any
    fields: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    vector: Optional[Vector] = None


class FieldSource(str, Enum):
    """필드 출처 타입."""

    AUTO = "AUTO"
    COLUMN = "COLUMN"
    PAYLOAD = "PAYLOAD"


class FilterOperator(str, Enum):
    """필터 연산자."""

    EQ = "EQ"
    NE = "NE"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"


class FilterCondition(BaseModel):
    """필터 조건."""

    field: str
    source: FieldSource = Field(default=FieldSource.AUTO)
    operator: FilterOperator
    value: Any


class FilterExpression(BaseModel):
    """필터 표현식."""

    conditions: List[FilterCondition] = Field(default_factory=list)
    logic: str = Field(default="AND", description="조건 결합 논리(AND/OR)")


class SortOrder(str, Enum):
    """정렬 순서."""

    ASC = "ASC"
    DESC = "DESC"


class SortField(BaseModel):
    """정렬 필드."""

    field: str
    source: FieldSource = Field(default=FieldSource.AUTO)
    order: SortOrder = SortOrder.ASC


class Pagination(BaseModel):
    """페이지네이션 정보."""

    limit: int = Field(default=50, ge=1)
    offset: int = Field(default=0, ge=0)


class Query(BaseModel):
    """일반 조회 쿼리 모델."""

    filter_expression: Optional[FilterExpression] = None
    sort: List[SortField] = Field(default_factory=list)
    pagination: Optional[Pagination] = None


class VectorSearchRequest(BaseModel):
    """벡터 검색 요청 모델."""

    collection: str
    vector: Vector
    top_k: int = Field(default=10, ge=1)
    filter_expression: Optional[FilterExpression] = None
    include_vectors: bool = Field(default=False)


class VectorSearchResult(BaseModel):
    """벡터 검색 결과 항목."""

    document: Document
    score: float


class VectorSearchResponse(BaseModel):
    """벡터 검색 응답 모델."""

    results: List[VectorSearchResult] = Field(default_factory=list)
    total: int = 0


class CollectionInfo(CollectionSchema):
    """이전 호환을 위한 컬렉션 정보 별칭."""
