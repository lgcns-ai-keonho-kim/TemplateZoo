"""
목적: Agent LangGraph 상태 타입을 정의한다.
설명: 의도 분류 기반 단일 요청 그래프 실행에 필요한 상태 구조를 제공한다.
디자인 패턴: 상태 객체(State Object)
참조: src/one_shot_agent/core/agent/graphs/agent_graph.py
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from one_shot_agent.core.agent.models import AgentMessage


class AgentGraphState(TypedDict):
    """LangGraph 단일 요청 상태 타입."""

    run_id: str
    user_message: str
    history: list[AgentMessage]

    intent_type_raw: NotRequired[str]
    intent_type: NotRequired[str]
    task_instruction: NotRequired[str]
    assistant_message: str
