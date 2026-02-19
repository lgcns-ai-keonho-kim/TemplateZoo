"""
목적: DB 엔진 구현체 모듈을 제공한다.
설명: 각 DB 엔진 클래스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/integrations/db/engines/*/engine.py
"""

from chatbot.integrations.db.engines.elasticsearch import ElasticsearchEngine
from chatbot.integrations.db.engines.mongodb import MongoDBEngine
from chatbot.integrations.db.engines.postgres import PostgresEngine
from chatbot.integrations.db.engines.redis import RedisEngine
from chatbot.integrations.db.engines.sqlite import SQLiteEngine

__all__ = [
    "SQLiteEngine",
    "RedisEngine",
    "ElasticsearchEngine",
    "MongoDBEngine",
    "PostgresEngine",
]
