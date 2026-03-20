"""
목적: Agent 라우터 공개 API를 제공한다.
설명: Agent 라우터 인스턴스를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_agent/api/agent/routers/router.py
"""

from one_shot_agent.api.agent.routers.router import router

__all__ = ["router"]
