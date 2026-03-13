"""
목적: LanceDB 엔진 공개 API를 제공한다.
설명: LanceDB 엔진 클래스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/single_request_tool_agent/integrations/db/engines/lancedb/engine.py
"""

from single_request_tool_agent.integrations.db.engines.lancedb.engine import (
    LanceDBEngine,
)

__all__ = ["LanceDBEngine"]
