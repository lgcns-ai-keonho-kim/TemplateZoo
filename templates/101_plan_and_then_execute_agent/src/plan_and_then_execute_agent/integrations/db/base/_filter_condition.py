"""
목적: DB 필터 조건 모델을 제공한다.
설명: 단일 필드 비교 조건을 표현하는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/plan_and_then_execute_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from plan_and_then_execute_agent.integrations.db.base._field_source import FieldSource
from plan_and_then_execute_agent.integrations.db.base._filter_operator import FilterOperator


class FilterCondition(BaseModel):
    """필터 조건."""

    field: str
    source: FieldSource = Field(default=FieldSource.AUTO)
    operator: FilterOperator
    value: Any

