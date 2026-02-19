"""
목적: UI 세션 조회 API 모델을 정의한다.
설명: UI 초기 렌더링과 세션 삭제 응답에 필요한 모델을 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/chatbot/api/ui/routers/router.py
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UISessionSummary(BaseModel):
    """UI 세션 요약 모델."""

    session_id: str
    title: str
    updated_at: datetime
    message_count: int
    last_message_preview: str | None = None


class UISessionListResponse(BaseModel):
    """UI 세션 목록 응답 모델."""

    sessions: list[UISessionSummary]
    limit: int
    offset: int


class UICreateSessionRequest(BaseModel):
    """UI 세션 생성 요청 모델."""

    title: str | None = Field(default=None, description="세션 제목")


class UICreateSessionResponse(BaseModel):
    """UI 세션 생성 응답 모델."""

    session_id: str


class UIDeleteSessionResponse(BaseModel):
    """UI 세션 삭제 응답 모델."""

    session_id: str
    deleted: bool = True
