"""
목적: Agent 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: 사용자 의도 분류 후 최종 응답을 생성하는 단일 요청 그래프를 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/single_request_agent/shared/agent/graph/base_agent_graph.py
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict

from single_request_agent.core.agent.models import AgentMessage
from single_request_agent.core.agent.nodes import (
    intent_classifier_node,
    intent_prepare_node,
    response_node,
)
from single_request_agent.core.agent.state import AgentGraphState
from single_request_agent.shared.agent.graph import BaseAgentGraph
from single_request_agent.shared.agent.interface import StreamNodeConfig
from single_request_agent.shared.logging import Logger, create_default_logger

logger: Logger = create_default_logger("AgentGraph")


class AgentGraphInput(BaseModel):
    """그래프 실행 입력 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    user_message: str
    history: list[AgentMessage]

    intent_type_raw: str = ""
    intent_type: str = ""
    task_instruction: str = ""
    assistant_message: str = ""


builder = StateGraph(cast(Any, AgentGraphState))
builder.add_node("intent_classify", intent_classifier_node.arun)
builder.add_node("intent_prepare", intent_prepare_node.run)
builder.add_node("response", response_node.arun)
builder.set_entry_point("intent_classify")
builder.add_edge("intent_classify", "intent_prepare")
builder.add_edge("intent_prepare", "response")
builder.add_edge("response", END)

stream_node: StreamNodeConfig = {
    "response": ["token", "assistant_message"],
}

agent_graph = BaseAgentGraph(
    builder=builder,
    stream_node=stream_node,
    logger=logger,
    input_model=AgentGraphInput,
)

__all__ = ["AgentGraphInput", "agent_graph"]
