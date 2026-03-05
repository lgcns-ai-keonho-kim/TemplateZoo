"""
목적: DB 벡터 검색 모델 공개 API 파사드를 제공한다.
설명: 벡터 검색 요청/결과/응답/호환 별칭 분리 구현을 재노출한다.
디자인 패턴: 퍼사드
참조: src/plan_and_then_execute_agent/integrations/db/base/_vector_search_request.py, src/plan_and_then_execute_agent/integrations/db/base/_collection_info.py
"""

from __future__ import annotations

from plan_and_then_execute_agent.integrations.db.base._collection_info import CollectionInfo
from plan_and_then_execute_agent.integrations.db.base._vector_search_request import (
    VectorSearchRequest,
)
from plan_and_then_execute_agent.integrations.db.base._vector_search_response import (
    VectorSearchResponse,
)
from plan_and_then_execute_agent.integrations.db.base._vector_search_result import VectorSearchResult

__all__ = [
    "VectorSearchRequest",
    "VectorSearchResult",
    "VectorSearchResponse",
    "CollectionInfo",
]

