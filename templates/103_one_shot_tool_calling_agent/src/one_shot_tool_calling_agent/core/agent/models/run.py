"""
목적: one shot tool calling agent 실행 결과 모델을 정의한다.
설명: API 응답과 서비스 내부 집계를 위한 실행 상태/Tool 추적 모델을 제공한다.
디자인 패턴: 값 객체(Value Object)
참조: src/one_shot_tool_calling_agent/shared/agent/services/agent_service.py
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentExecutionStatus(str, Enum):
    """one shot tool calling agent 실행 상태."""

    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class AgentToolTrace(BaseModel):
    """Tool 실행 추적 결과."""

    tool_name: str
    status: Literal["SUCCESS", "FAILED"]
    output: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    attempt: int = 1


class AgentRunResult(BaseModel):
    """one shot tool calling agent 실행 결과."""

    run_id: str
    status: AgentExecutionStatus
    output_text: str
    tool_results: list[AgentToolTrace] = Field(default_factory=list)
