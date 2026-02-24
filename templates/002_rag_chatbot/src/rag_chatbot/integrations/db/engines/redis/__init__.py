"""
목적: Redis 엔진 공개 API를 제공한다.
설명: Redis 엔진 클래스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/integrations/db/engines/redis/engine.py
"""

from rag_chatbot.integrations.db.engines.redis.engine import RedisEngine

__all__ = ["RedisEngine"]
