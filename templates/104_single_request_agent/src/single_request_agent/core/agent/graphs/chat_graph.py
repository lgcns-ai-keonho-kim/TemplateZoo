"""
목적: Chat 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: 사용자 의도 분류 후 최종 응답을 생성하는 단일 요청 그래프를 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/single_request_agent/shared/agent/graph/base_chat_graph.py
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict

from single_request_agent.core.agent.models import ChatMessage
from single_request_agent.core.agent.nodes import (
    intent_classifier_node,
    intent_prepare_node,
    response_node,
)
from single_request_agent.core.agent.state import ChatGraphState
from single_request_agent.shared.agent.graph import BaseChatGraph
from single_request_agent.shared.agent.interface import StreamNodeConfig
from single_request_agent.shared.logging import Logger, create_default_logger

logger: Logger = create_default_logger("ChatGraph")


class ChatGraphInput(BaseModel):
    """그래프 실행 입력 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    request_id: str = ""
    user_message: str
    history: list[ChatMessage]

    intent_type_raw: str = ""
    intent_type: str = ""
    task_instruction: str = ""
    assistant_message: str = ""


# 그래프 선언
builder = StateGraph(cast(Any, ChatGraphState))

# 노드 추가
builder.add_node("intent_classify", intent_classifier_node.arun)
builder.add_node("intent_prepare", intent_prepare_node.run)
builder.add_node("response", response_node.arun)

# 진입점 설정
builder.set_entry_point("intent_classify")

# 엣지 설정
builder.add_edge("intent_classify", "intent_prepare")
builder.add_edge("intent_prepare", "response")
builder.add_edge("response", END)

# 그래프 설정 정의

# Stream 할 노드 정의
stream_node: StreamNodeConfig = {
    "response": ["token", "assistant_message"],
}

chat_graph = BaseChatGraph(
    builder=builder,
    stream_node=stream_node,
    logger=logger,
    input_model=ChatGraphInput,
)
