"""
목적: DB 벡터 검색 요청 모델을 제공한다.
설명: 벡터 검색 입력 파라미터를 담는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from one_shot_agent.integrations.db.base._filter_expression import (
    FilterExpression,
)
from one_shot_agent.integrations.db.base._vector import Vector


class VectorSearchRequest(BaseModel):
    """벡터 검색 요청 모델."""

    collection: str
    vector: Vector
    top_k: int = Field(default=10, ge=1)
    filter_expression: Optional[FilterExpression] = None
    include_vectors: bool = Field(default=False)
    vector_field: Optional[str] = Field(
        default=None,
        description="검색 대상 벡터 필드명(None이면 스키마 기본 vector_field 사용)",
    )
