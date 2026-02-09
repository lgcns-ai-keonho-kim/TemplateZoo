"""
목적: Chat 큐 API 모델을 정의한다.
설명: 세션 메시지 큐 등록 요청/응답 모델을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/api/chat/routers/chat.py
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from base_template.core.chat.const import DEFAULT_CONTEXT_WINDOW


class QueueMessageRequest(BaseModel):
    """세션 메시지 큐 등록 요청 모델."""

    message: str = Field(..., min_length=1, description="사용자 메시지 본문")
    context_window: int = Field(
        default=DEFAULT_CONTEXT_WINDOW,
        ge=1,
        le=100,
        description="응답 생성 시 참고할 최근 메시지 개수",
    )


class QueueMessageResponse(BaseModel):
    """세션 메시지 큐 등록 응답 모델."""

    session_id: str
    task_id: str
    queued_at: datetime
