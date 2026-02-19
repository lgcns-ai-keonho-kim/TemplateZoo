"""
목적: Chat 메시지 API 모델을 정의한다.
설명: 메시지 조회 및 결과 표현 모델을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/chatbot/api/chat/routers/router.py
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from chatbot.core.chat.models import ChatRole


class MessageResponse(BaseModel):
    """메시지 응답 모델."""

    message_id: str
    role: ChatRole
    content: str
    sequence: int
    created_at: datetime


class MessageListResponse(BaseModel):
    """메시지 목록 응답 모델."""

    session_id: str
    messages: list[MessageResponse]
    limit: int
    offset: int
