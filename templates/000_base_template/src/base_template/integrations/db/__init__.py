"""
목적: DB 통합 모듈 공개 API를 제공한다.
설명: 엔진 구현체와 공통 클라이언트를 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/integrations/db/engines
"""

from .client import DBClient
from .query_builder import DeleteBuilder
from .engines import (
    ElasticSearchEngine,
    MongoDBEngine,
    MySQLEngine,
    PostgresEngine,
    RedisEngine,
    SqliteVectorEngine,
)
from .query_builder import ReadBuilder
from .query_builder import WriteBuilder

__all__ = [
    "DBClient",
    "ReadBuilder",
    "WriteBuilder",
    "DeleteBuilder",
    "SqliteVectorEngine",
    "RedisEngine",
    "ElasticSearchEngine",
    "MongoDBEngine",
    "PostgresEngine",
    "MySQLEngine",
]
