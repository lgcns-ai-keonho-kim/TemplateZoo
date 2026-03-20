"""
목적: DB 컬럼 스펙 모델을 제공한다.
설명: 컬럼 이름/타입/벡터 속성 등 스키마 필드를 표현한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/tool_proxy_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional

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
