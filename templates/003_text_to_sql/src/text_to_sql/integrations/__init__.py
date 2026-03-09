"""
목적: integrations 패키지의 공개 API를 제공한다.
설명: DB/LLM 통합 모듈을 한 번에 노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/integrations/db, src/text_to_sql/integrations/llm, src/text_to_sql/integrations/embedding
"""

from text_to_sql.integrations.db import (
    DBClient,
    DeleteBuilder,
    ElasticsearchEngine,
    LanceDBEngine,
    MongoDBEngine,
    PostgresEngine,
    ReadBuilder,
    RedisEngine,
    SQLiteEngine,
    WriteBuilder,
)
from text_to_sql.integrations.embedding import EmbeddingClient
from text_to_sql.integrations.llm import LLMClient

__all__ = [
    "DBClient",
    "ReadBuilder",
    "WriteBuilder",
    "DeleteBuilder",
    "LanceDBEngine",
    "SQLiteEngine",
    "RedisEngine",
    "ElasticsearchEngine",
    "MongoDBEngine",
    "PostgresEngine",
    "LLMClient",
    "EmbeddingClient",
]
