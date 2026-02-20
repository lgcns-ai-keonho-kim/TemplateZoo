"""
목적: DB 베이스 모듈 공개 API를 제공한다.
설명: 공통 모델과 엔진/세션/풀 인터페이스를 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/integrations/db/base/models.py, src/rag_chatbot/integrations/db/base/engine.py
"""

from rag_chatbot.integrations.db.base.engine import BaseDBEngine
from rag_chatbot.integrations.db.base.models import (
    CollectionInfo,
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    FilterCondition,
    FilterExpression,
    FilterOperator,
    Pagination,
    Query,
    SortField,
    SortOrder,
    Vector,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from rag_chatbot.integrations.db.base.pool import BaseConnectionPool
from rag_chatbot.integrations.db.base.query_builder import QueryBuilder
from rag_chatbot.integrations.db.base.session import BaseSession

__all__ = [
    "CollectionInfo",
    "CollectionSchema",
    "ColumnSpec",
    "Document",
    "FieldSource",
    "FilterCondition",
    "FilterExpression",
    "FilterOperator",
    "Pagination",
    "Query",
    "SortField",
    "SortOrder",
    "Vector",
    "VectorSearchRequest",
    "VectorSearchResult",
    "VectorSearchResponse",
    "BaseDBEngine",
    "BaseSession",
    "BaseConnectionPool",
    "QueryBuilder",
]
