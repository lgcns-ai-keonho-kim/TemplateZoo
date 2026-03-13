"""
목적: DB 필터 표현식 모델을 제공한다.
설명: 다수 조건과 결합 논리를 포함하는 조회 필터 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/single_request_tool_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from single_request_tool_agent.integrations.db.base._filter_condition import (
    FilterCondition,
)


class FilterExpression(BaseModel):
    """필터 표현식."""

    conditions: List[FilterCondition] = Field(default_factory=list)
    logic: str = Field(default="AND", description="조건 결합 논리(AND/OR)")
