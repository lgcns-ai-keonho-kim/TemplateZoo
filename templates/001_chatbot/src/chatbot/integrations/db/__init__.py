"""
목적: DB 통합 모듈 공개 API를 제공한다.
설명: 엔진 구현체와 공통 클라이언트를 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/integrations/db/engines
"""

from chatbot.integrations.db.client import DBClient
from chatbot.integrations.db.query_builder import DeleteBuilder
from chatbot.integrations.db.engines import (
    ElasticsearchEngine,
    MongoDBEngine,
    PostgresEngine,
    RedisEngine,
    SQLiteEngine,
)
from chatbot.integrations.db.query_builder import ReadBuilder
from chatbot.integrations.db.query_builder import WriteBuilder

__all__ = [
    "DBClient",
    "ReadBuilder",
    "WriteBuilder",
    "DeleteBuilder",
    "SQLiteEngine",
    "RedisEngine",
    "ElasticsearchEngine",
    "MongoDBEngine",
    "PostgresEngine",
]
