"""
목적: 1회성 Agent 실행 결과 모델을 정의한다.
설명: API 응답과 서비스 내부 집계를 위한 실행 상태와 최종 응답 본문을 제공한다.
디자인 패턴: 값 객체(Value Object)
참조: src/single_request_agent/shared/agent/services/agent_service.py
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class AgentExecutionStatus(str, Enum):
    """1회성 Agent 실행 상태."""

    COMPLETED = "COMPLETED"


class AgentRunResult(BaseModel):
    """1회성 Agent 실행 결과."""

    run_id: str
    status: AgentExecutionStatus
    output_text: str
