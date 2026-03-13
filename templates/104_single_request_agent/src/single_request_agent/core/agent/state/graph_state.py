"""
목적: Chat LangGraph 상태 타입을 정의한다.
설명: 의도 분류 기반 단일 요청 그래프 실행에 필요한 상태 구조를 제공한다.
디자인 패턴: 상태 객체(State Object)
참조: src/single_request_agent/core/agent/graphs/chat_graph.py
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from single_request_agent.core.agent.models import ChatMessage


class ChatGraphState(TypedDict):
    """LangGraph 대화 상태 타입."""

    session_id: str
    request_id: NotRequired[str]
    user_message: str
    history: list[ChatMessage]

    intent_type_raw: NotRequired[str]
    intent_type: NotRequired[str]
    task_instruction: NotRequired[str]
    assistant_message: str
