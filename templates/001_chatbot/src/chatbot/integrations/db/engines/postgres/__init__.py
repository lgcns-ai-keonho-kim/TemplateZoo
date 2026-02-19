"""
목적: PostgreSQL 엔진 공개 API를 제공한다.
설명: PostgreSQL 엔진 클래스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/chatbot/integrations/db/engines/postgres/engine.py
"""

from chatbot.integrations.db.engines.postgres.engine import PostgresEngine

__all__ = ["PostgresEngine"]
