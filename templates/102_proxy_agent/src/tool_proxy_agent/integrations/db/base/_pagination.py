"""
목적: DB 페이지네이션 모델을 제공한다.
설명: 조회 limit/offset을 표현하는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/tool_proxy_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Pagination(BaseModel):
    """페이지네이션 정보."""

    limit: int = Field(default=50, ge=1)
    offset: int = Field(default=0, ge=0)
