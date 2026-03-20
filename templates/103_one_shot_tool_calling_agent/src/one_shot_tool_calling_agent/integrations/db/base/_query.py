"""
목적: DB 일반 조회 쿼리 모델을 제공한다.
설명: 필터/정렬/페이지네이션 정보를 담는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_tool_calling_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from one_shot_tool_calling_agent.integrations.db.base._filter_expression import (
    FilterExpression,
)
from one_shot_tool_calling_agent.integrations.db.base._pagination import Pagination
from one_shot_tool_calling_agent.integrations.db.base._sort_field import SortField


class Query(BaseModel):
    """일반 조회 쿼리 모델."""

    filter_expression: Optional[FilterExpression] = None
    sort: List[SortField] = Field(default_factory=list)
    pagination: Optional[Pagination] = None
