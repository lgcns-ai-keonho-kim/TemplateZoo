"""
목적: DB 문서 모델을 제공한다.
설명: 문서 ID/필드/페이로드/벡터를 담는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from one_shot_agent.integrations.db.base._vector import Vector


class Document(BaseModel):
    """문서 데이터를 표현한다."""

    doc_id: Any
    fields: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    vector: Optional[Vector] = None
