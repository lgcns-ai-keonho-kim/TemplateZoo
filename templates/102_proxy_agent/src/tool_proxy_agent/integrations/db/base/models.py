"""
목적: DB 공통 모델 공개 API 파사드를 제공한다.
설명: 분리된 모델 구현 파일을 단일 진입점으로 재노출한다.
디자인 패턴: 퍼사드
참조: src/tool_proxy_agent/integrations/db/base/_models_schema.py, src/tool_proxy_agent/integrations/db/base/_models_document.py
"""

from __future__ import annotations

from tool_proxy_agent.integrations.db.base._models_document import (
    Document,
    Vector,
)
from tool_proxy_agent.integrations.db.base._models_filter import (
    FieldSource,
    FilterCondition,
    FilterExpression,
    FilterOperator,
)
from tool_proxy_agent.integrations.db.base._models_query import (
    Pagination,
    Query,
    SortField,
    SortOrder,
)
from tool_proxy_agent.integrations.db.base._models_schema import (
    CollectionSchema,
    ColumnSpec,
)
from tool_proxy_agent.integrations.db.base._models_vector_search import (
    CollectionInfo,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)

__all__ = [
    "ColumnSpec",
    "CollectionSchema",
    "Vector",
    "Document",
    "FieldSource",
    "FilterOperator",
    "FilterCondition",
    "FilterExpression",
    "SortOrder",
    "SortField",
    "Pagination",
    "Query",
    "VectorSearchRequest",
    "VectorSearchResult",
    "VectorSearchResponse",
    "CollectionInfo",
]
