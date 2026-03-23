"""
목적: 1회성 Agent API 요청/응답 모델을 정의한다.
설명: `/agent` 단일 실행 엔드포인트가 사용하는 DTO를 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/one_shot_agent/api/agent/routers/router.py
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RunAgentRequest(BaseModel):
    """1회성 Agent 실행 요청 모델."""

    request: str = Field(..., min_length=1, description="사용자 단일 요청 본문")


class RunAgentResponse(BaseModel):
    """1회성 Agent 실행 응답 모델."""

    run_id: str
    status: Literal["COMPLETED"]
    output_text: str
