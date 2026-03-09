"""
목적: DB 통합 모듈 공개 API를 제공한다.
설명: 엔진 구현체와 공통 클라이언트를 노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/integrations/db/engines
"""

from text_to_sql.integrations.db.client import DBClient
from text_to_sql.integrations.db.query_target_registry import (
    QueryTarget,
    QueryTargetRegistry,
)
from text_to_sql.integrations.db.query_builder import DeleteBuilder
from text_to_sql.integrations.db.query_builder import AggregateReadBuilder
from text_to_sql.integrations.db.engines import (
    ElasticsearchEngine,
    LanceDBEngine,
    MongoDBEngine,
    PostgresEngine,
    RedisEngine,
    SQLiteEngine,
)
from text_to_sql.integrations.db.query_builder import ReadBuilder
from text_to_sql.integrations.db.query_builder import WriteBuilder

__all__ = [
    "DBClient",
    "QueryTarget",
    "QueryTargetRegistry",
    "ReadBuilder",
    "AggregateReadBuilder",
    "WriteBuilder",
    "DeleteBuilder",
    "LanceDBEngine",
    "SQLiteEngine",
    "RedisEngine",
    "ElasticsearchEngine",
    "MongoDBEngine",
    "PostgresEngine",
]
