"""
목적: integrations 패키지의 공개 API를 제공한다.
설명: DB/LLM 통합 모듈을 한 번에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_agent/integrations/db, src/one_shot_agent/integrations/llm, src/one_shot_agent/integrations/embedding
"""

from one_shot_agent.integrations.db import (
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
from one_shot_agent.integrations.embedding import EmbeddingClient
from one_shot_agent.integrations.llm import LLMClient

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
