"""
목적: Chat 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: safeguard -> response/blocked 분기 그래프를 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/base_template/shared/chat/graph/base_chat_graph.py
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict

from base_template.core.chat.models import ChatMessage
from base_template.core.chat.nodes import (
    response_node,
    safeguard_message_node,
    safeguard_route_node,
    safeguard_node,
)
from base_template.core.chat.state import ChatGraphState
from base_template.shared.chat.graph import BaseChatGraph
from base_template.shared.chat.interface import StreamNodeConfig
from base_template.shared.logging import Logger, create_default_logger

logger: Logger = create_default_logger("ChatGraph")


class ChatGraphInput(BaseModel):
    """그래프 실행 입력 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_message: str
    history: list[ChatMessage]
    safeguard_result: str | None = None
    safeguard_route: str | None = None
    assistant_message: str = ""


builder = StateGraph(ChatGraphState)
builder.add_node("safeguard", safeguard_node.run)
builder.add_node("safeguard_route", safeguard_route_node.run)
builder.add_node("response", response_node.run)
builder.add_node("blocked", safeguard_message_node.run)
builder.set_entry_point("safeguard")
builder.add_edge("safeguard", "safeguard_route")
builder.add_conditional_edges(
    "safeguard_route",
    lambda state: str(state.get("safeguard_route") or "blocked"),
    {
        "response": "response",
        "blocked": "blocked",
    },
)
builder.add_edge("response", END)
builder.add_edge("blocked", END)

checkpointer = None
stream_node: StreamNodeConfig = {
    "safeguard": ["safeguard_result"],
    "safeguard_route": ["safeguard_route", "safeguard_result"],
    "response": ["token", "assistant_message"],
    "blocked": ["assistant_message"],
}

chat_graph = BaseChatGraph(
    builder=builder,
    checkpointer=checkpointer,
    stream_node=stream_node,
    logger=logger,
    input_model=ChatGraphInput,
)
