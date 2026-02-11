"""
목적: Chat 단일 스트림 API 모델을 정의한다.
설명: 스트림 요청 모델과 SSE 이벤트 페이로드를 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/api/chat/routers/stream_session_message.py
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from base_template.core.chat.const import DEFAULT_CONTEXT_WINDOW


class StreamEventType(str, Enum):
    """SSE 이벤트 타입."""

    START = "start"
    TOKEN = "token"
    DONE = "done"
    ERROR = "error"


class StreamMessageRequest(BaseModel):
    """단일 스트림 메시지 요청 모델."""

    message: str = Field(..., min_length=1, description="사용자 메시지 본문")
    context_window: int = Field(
        default=DEFAULT_CONTEXT_WINDOW,
        ge=1,
        le=100,
        description="응답 생성 시 참고할 최근 메시지 개수",
    )


class StreamPayload(BaseModel):
    """SSE data 페이로드 모델."""

    session_id: str
    type: StreamEventType
    content: str = ""
    node: str | None = None
    event: str | None = None
    status: str | None = None
    error_message: str | None = None
