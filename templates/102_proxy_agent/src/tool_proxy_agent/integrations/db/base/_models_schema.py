"""
목적: DB 스키마 모델 공개 API 파사드를 제공한다.
설명: 컬럼/컬렉션 스키마 분리 구현을 단일 진입점으로 재노출한다.
디자인 패턴: 퍼사드
참조: src/tool_proxy_agent/integrations/db/base/_column_spec.py, src/tool_proxy_agent/integrations/db/base/_collection_schema.py
"""

from __future__ import annotations

from tool_proxy_agent.integrations.db.base._collection_schema import (
    CollectionSchema,
)
from tool_proxy_agent.integrations.db.base._column_spec import ColumnSpec

__all__ = ["ColumnSpec", "CollectionSchema"]
