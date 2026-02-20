"""
목적: Chat LangGraph 상태 타입을 정의한다.
설명: 그래프 실행 시 입력/출력으로 전달되는 최소 상태 구조를 제공한다.
디자인 패턴: 상태 객체(State Object)
참조: src/rag_chatbot/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from typing import NotRequired, TypedDict

from rag_chatbot.core.chat.models import ChatMessage


class ChatGraphState(TypedDict):
    """LangGraph 대화 상태 타입."""

    session_id: str
    user_message: str
    history: list[ChatMessage]
    safeguard_result: NotRequired[str]
    safeguard_route: NotRequired[str]
    safeguard_reason: NotRequired[str]
    rag_context: NotRequired[str]
    rag_references: NotRequired[list[dict[str, object]]]
    assistant_message: str
