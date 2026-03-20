"""
목적: DB 벡터 검색 응답 모델을 제공한다.
설명: 결과 목록과 총 개수를 담는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from one_shot_agent.integrations.db.base._vector_search_result import (
    VectorSearchResult,
)


class VectorSearchResponse(BaseModel):
    """벡터 검색 응답 모델."""

    results: List[VectorSearchResult] = Field(default_factory=list)
    total: int = 0
