"""
목적: DB 벡터 검색 결과 항목 모델을 제공한다.
설명: 검색된 문서와 유사도 점수를 담는 DTO를 정의한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from pydantic import BaseModel

from one_shot_agent.integrations.db.base._document import Document


class VectorSearchResult(BaseModel):
    """벡터 검색 결과 항목."""

    document: Document
    score: float
