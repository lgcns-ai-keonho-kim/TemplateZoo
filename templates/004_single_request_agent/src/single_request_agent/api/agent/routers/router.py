"""
목적: Agent API 라우터 집계를 제공한다.
설명: 1회성 Agent 실행 라우터를 하나의 공개 경계로 묶는다.
디자인 패턴: 컴포지트 패턴
참조: src/single_request_agent/api/agent/routers/run_agent.py
"""

from __future__ import annotations

from fastapi import APIRouter

from single_request_agent.api.const import AGENT_API_PREFIX, AGENT_API_TAG
from single_request_agent.api.agent.routers.run_agent import (
    router as run_agent_router,
)

router = APIRouter(tags=[AGENT_API_TAG])
router.include_router(run_agent_router, prefix=AGENT_API_PREFIX)
