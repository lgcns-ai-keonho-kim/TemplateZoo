"""
목적: Chat 스트림 이벤트 모델을 정의한다.
설명: SSE 스트림 이벤트 타입과 페이로드 모델을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/api/chat/routers/chat.py
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from base_template.api.chat.models.message import MessageResponse


class StreamEventType(str, Enum):
    """SSE 이벤트 타입."""

    START = "start"
    TOKEN = "token"
    DONE = "done"
    ERROR = "error"


class StreamPayload(BaseModel):
    """SSE data 페이로드 모델."""

    session_id: str
    task_id: str
    type: StreamEventType
    content: str = ""
    error_message: str | None = None
    status: str | None = None
    final_content: str | None = None
    assistant_message: MessageResponse | None = None
