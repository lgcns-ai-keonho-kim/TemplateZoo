"""
목적: Chat 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: safeguard -> rag -> response / blocked 분기 그래프를 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/rag_chatbot/shared/chat/graph/base_chat_graph.py
"""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from rag_chatbot.core.chat.models import ChatMessage
from rag_chatbot.core.chat.nodes import (
    rag_node,
    response_node,
    safeguard_message_node,
    safeguard_route_node,
    safeguard_node,
)
from rag_chatbot.core.chat.state import ChatGraphState
from rag_chatbot.shared.chat.graph import BaseChatGraph
from rag_chatbot.shared.chat.interface import StreamNodeConfig
from rag_chatbot.shared.logging import Logger, create_default_logger

logger: Logger = create_default_logger("ChatGraph")


class ChatGraphInput(BaseModel):
    """그래프 실행 입력 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_message: str
    history: list[ChatMessage]
    safeguard_result: str | None = None
    safeguard_route: str | None = None
    rag_context: str = ""
    rag_references: list[dict[str, object]] = Field(default_factory=list)
    assistant_message: str = ""


# 그래프 선언
builder = StateGraph(ChatGraphState)
# 노드 추가
builder.add_node("safeguard", safeguard_node.run)
builder.add_node("safeguard_route", safeguard_route_node.run)
builder.add_node("rag", rag_node.run)
builder.add_node("response", response_node.run)
builder.add_node("blocked", safeguard_message_node.run)
# 진입점 설정
builder.set_entry_point("safeguard")
# 엣지 설정
builder.add_edge("safeguard", "safeguard_route")
builder.add_conditional_edges(
    "safeguard_route",
    lambda state: str(state.get("safeguard_route") or "blocked"),
    {
        "response": "rag",
        "blocked": "blocked",
    },
)
builder.add_edge("rag", "response")
builder.add_edge("response", END)
builder.add_edge("blocked", END)

# 그래프 설정 정의

# Checkpointer 정의
checkpointer = InMemorySaver()

# Stream 할 노드 정의
stream_node: StreamNodeConfig = {
    "safeguard": ["safeguard_result"],
    "safeguard_route": ["safeguard_route", "safeguard_result"],
    "rag": ["rag_context", "rag_references"],
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
