"""
목적: Chat 요청/스트림 API 모델을 정의한다.
설명: 작업 제출, 세션 스냅샷, SSE 이벤트 페이로드 모델을 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/api/chat/routers/create_chat.py
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from base_template.api.chat.models.message import MessageResponse
from base_template.core.chat.const import DEFAULT_CONTEXT_WINDOW


class StreamEventType(str, Enum):
    """SSE 이벤트 타입."""

    START = "start"
    TOKEN = "token"
    DONE = "done"
    ERROR = "error"


class SubmitChatRequest(BaseModel):
    """채팅 작업 제출 요청 모델."""

    session_id: str | None = Field(default=None, description="기존 세션 식별자(없으면 신규 생성)")
    message: str = Field(..., min_length=1, description="사용자 메시지 본문")
    context_window: int = Field(
        default=DEFAULT_CONTEXT_WINDOW,
        ge=1,
        le=100,
        description="응답 생성 시 참고할 최근 메시지 개수",
    )


class SubmitChatResponse(BaseModel):
    """채팅 작업 제출 응답 모델."""

    session_id: str
    request_id: str
    status: Literal["QUEUED"] = "QUEUED"


class SessionSnapshotResponse(BaseModel):
    """세션 상태/메시지 스냅샷 응답 모델."""

    session_id: str
    messages: list[MessageResponse]
    last_status: str | None = None
    updated_at: datetime | None = None


class StreamPayload(BaseModel):
    """SSE data 페이로드 모델."""

    session_id: str
    request_id: str
    type: StreamEventType
    node: str
    content: str = ""
    status: str | None = None
    error_message: str | None = None
    metadata: dict[str, object] | None = None
