"""
목적: Chat 턴 처리 결과 모델을 정의한다.
설명: 사용자 입력 1턴 처리의 산출물(세션/사용자 메시지/어시스턴트 메시지)을 묶어 제공한다.
디자인 패턴: DTO 패턴
참조: src/rag_chatbot/shared/chat/services/chat_service.py
"""

from __future__ import annotations

from pydantic import BaseModel

from rag_chatbot.core.chat.models.entities import ChatMessage, ChatSession


class ChatTurnResult(BaseModel):
    """사용자 1턴 처리 결과 모델."""

    session: ChatSession
    user_message: ChatMessage
    assistant_message: ChatMessage
