"""
목적: DB 벡터 모델을 제공한다.
설명: 벡터 값과 차원 정보를 표현하는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Vector(BaseModel):
    """벡터 데이터를 표현한다."""

    values: List[float]
    dimension: Optional[int] = None
