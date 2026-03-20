"""
목적: DB 정렬 필드 모델을 제공한다.
설명: 정렬 대상 필드와 출처/정렬 방향을 표현하는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_tool_calling_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from one_shot_tool_calling_agent.integrations.db.base._field_source import FieldSource
from one_shot_tool_calling_agent.integrations.db.base._sort_order import SortOrder


class SortField(BaseModel):
    """정렬 필드."""

    field: str
    source: FieldSource = Field(default=FieldSource.AUTO)
    order: SortOrder = SortOrder.ASC
