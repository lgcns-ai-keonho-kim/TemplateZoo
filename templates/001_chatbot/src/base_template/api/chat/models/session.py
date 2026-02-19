"""
목적: Chat 세션 API 모델을 정의한다.
설명: 세션 생성/목록 조회 요청과 응답 모델을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/api/chat/routers/router.py
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """세션 생성 요청 모델."""

    title: Optional[str] = Field(default=None, description="세션 제목")


class CreateSessionResponse(BaseModel):
    """세션 생성 응답 모델."""

    session_id: str


class SessionSummaryResponse(BaseModel):
    """세션 목록 요약 항목 모델."""

    session_id: str
    title: str
    updated_at: datetime
    message_count: int
    last_message_preview: str | None = None


class SessionListResponse(BaseModel):
    """세션 목록 응답 모델."""

    sessions: list[SessionSummaryResponse]
    limit: int
    offset: int
