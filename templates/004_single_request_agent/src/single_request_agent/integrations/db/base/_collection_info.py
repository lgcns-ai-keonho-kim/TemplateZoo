"""
목적: DB 컬렉션 정보 호환 모델을 제공한다.
설명: 기존 호환을 위해 CollectionSchema 별칭 클래스를 유지한다.
디자인 패턴: 별칭 래퍼
참조: src/single_request_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from single_request_agent.integrations.db.base._collection_schema import (
    CollectionSchema,
)


class CollectionInfo(CollectionSchema):
    """이전 호환을 위한 컬렉션 정보 별칭."""
