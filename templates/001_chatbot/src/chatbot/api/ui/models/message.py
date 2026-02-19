"""
목적: UI 메시지 조회 API 모델을 정의한다.
설명: 세션별 메시지 이력 렌더링에 필요한 응답 모델을 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/chatbot/api/ui/routers/router.py
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from chatbot.core.chat.models import ChatRole


class UIMessageItem(BaseModel):
    """UI 메시지 항목 모델."""

    message_id: str
    role: ChatRole
    content: str
    sequence: int
    created_at: datetime


class UIMessageListResponse(BaseModel):
    """UI 메시지 목록 응답 모델."""

    session_id: str
    messages: list[UIMessageItem]
    limit: int
    offset: int
