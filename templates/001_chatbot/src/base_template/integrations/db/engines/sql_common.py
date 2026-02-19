"""
목적: SQL 계열 엔진에서 공통으로 사용하는 유틸리티를 제공한다.
설명: 스키마 보정, 필드 출처 결정, 컬럼 선택, 식별자 인용 로직을 통합한다.
디자인 패턴: 유틸리티 모듈
참조: src/base_template/integrations/db/base/models.py
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional

from base_template.integrations.db.base.models import (
    CollectionSchema,
    FieldSource,
)


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SQLIdentifierHelper:
    """SQL 식별자 검증/인용 도우미."""

    def quote_identifier(self, name: str) -> str:
        """식별자를 검증하고 쌍따옴표로 감싸 반환한다."""

        if not name:
            raise ValueError("식별자 이름이 비어 있습니다.")
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"허용되지 않는 식별자: {name}")
        return f'"{name}"'

    def quote_table(self, name: str) -> str:
        """테이블 식별자를 반환한다."""

        return self.quote_identifier(name)

    def plain_identifier(self, name: str) -> str:
        """인용 없는 식별자를 검증해 반환한다."""

        if not name:
            raise ValueError("식별자 이름이 비어 있습니다.")
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"허용되지 않는 식별자: {name}")
        return name


def ensure_schema(
    schema: Optional[CollectionSchema],
    collection: Optional[str] = None,
) -> CollectionSchema:
    """입력 스키마를 보정해 반환한다."""

    if schema is not None:
        return schema
    if collection is None:
        raise ValueError("컬렉션 이름이 필요합니다.")
    return CollectionSchema.default(collection)


def resolve_source(
    source: FieldSource,
    field: str,
    schema: CollectionSchema,
) -> FieldSource:
    """필드 출처를 확정한다."""

    return schema.resolve_source(field, source)


def select_columns(
    schema: CollectionSchema,
    include_vector: bool = False,
) -> Optional[List[str]]:
    """조회 시 선택할 컬럼 목록을 반환한다."""

    if not schema.columns:
        return None
    names = schema.column_names()
    if schema.primary_key not in names:
        names.insert(0, schema.primary_key)
    if schema.payload_field and schema.payload_field not in names:
        names.append(schema.payload_field)
    if include_vector and schema.vector_field and schema.vector_field not in names:
        names.append(schema.vector_field)
    return names


def select_sql(
    columns: Optional[List[str]],
    quote_identifier: Callable[[str], str],
) -> str:
    """SELECT 컬럼 SQL 표현식을 반환한다."""

    if not columns:
        return "*"
    return ", ".join(quote_identifier(name) for name in columns)


def payload_field(schema: CollectionSchema) -> str:
    """payload 필드명을 반환한다."""

    if not schema.payload_field:
        raise RuntimeError("payload 필드가 정의되어 있지 않습니다.")
    return schema.payload_field


def vector_field(schema: CollectionSchema) -> Optional[str]:
    """벡터 필드명을 반환한다."""

    return schema.vector_field or None


def vector_dimension(schema: CollectionSchema) -> int:
    """벡터 차원을 반환한다."""

    dimension = schema.resolve_vector_dimension()
    if dimension is None:
        raise ValueError("벡터 차원 정보가 필요합니다.")
    return dimension
