"""
목적: DB 통합 모듈 공개 API를 제공한다.
설명: 엔진 구현체와 공통 클라이언트를 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/integrations/db/engines
"""

from base_template.integrations.db.client import DBClient
from base_template.integrations.db.query_builder import DeleteBuilder
from base_template.integrations.db.engines import (
    ElasticSearchEngine,
    MongoDBEngine,
    PostgresEngine,
    RedisEngine,
    SqliteVectorEngine,
)
from base_template.integrations.db.query_builder import ReadBuilder
from base_template.integrations.db.query_builder import WriteBuilder

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
]
