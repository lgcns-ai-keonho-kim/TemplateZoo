"""
목적: 1회성 Agent API 요청/응답 모델을 정의한다.
설명: `/agent` 단일 실행 엔드포인트가 사용하는 DTO를 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/single_request_tool_agent/api/agent/routers/router.py
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RunAgentRequest(BaseModel):
    """1회성 Agent 실행 요청 모델."""

    request: str = Field(..., min_length=1, description="사용자 단일 요청 본문")


class ToolResultItem(BaseModel):
    """Tool 실행 결과 응답 모델."""

    tool_name: str
    status: Literal["SUCCESS", "FAILED"]
    output: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    attempt: int


class RunAgentResponse(BaseModel):
    """1회성 Agent 실행 응답 모델."""

    run_id: str
    status: Literal["COMPLETED", "BLOCKED"]
    output_text: str
    tool_results: list[ToolResultItem] = Field(default_factory=list)
