"""
목적: MongoDB 엔진 공개 API를 제공한다.
설명: MongoDB 엔진 클래스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/plan_and_then_execute_agent/integrations/db/engines/mongodb/engine.py
"""

from plan_and_then_execute_agent.integrations.db.engines.mongodb.engine import MongoDBEngine

__all__ = ["MongoDBEngine"]
