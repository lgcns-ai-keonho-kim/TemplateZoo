"""
목적: Chat 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: safeguard -> tool selector -> tool execute -> retry -> response 흐름을 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/single_request_tool_agent/shared/agent/graph/base_chat_graph.py
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from single_request_tool_agent.core.agent.models import ChatMessage
from single_request_tool_agent.core.agent.nodes import (
    response_node,
    response_prepare_node,
    retry_llm_node,
    retry_parse_node,
    retry_prepare_node,
    retry_route_node,
    retry_validate_node,
    safeguard_message_node,
    safeguard_route_node,
    safeguard_node,
    tool_exec_node,
    tool_execute_collect_node,
    tool_execute_fanout_branch_node,
    tool_execute_fanout_route_node,
    tool_execute_prepare_node,
    tool_execute_route_node,
    tool_selector_llm_node,
    tool_selector_parse_node,
    tool_selector_prepare_node,
    tool_selector_validate_node,
)
from single_request_tool_agent.core.agent.state import ChatGraphState
from single_request_tool_agent.shared.agent.graph import BaseChatGraph
from single_request_tool_agent.shared.agent.interface import StreamNodeConfig
from single_request_tool_agent.shared.logging import Logger, create_default_logger

logger: Logger = create_default_logger("ChatGraph")


class ChatGraphInput(BaseModel):
    """그래프 실행 입력 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    request_id: str = ""
    user_message: str
    history: list[ChatMessage]

    safeguard_result: str | None = None
    safeguard_route: str | None = None

    tool_catalog_payload: str = ""
    tool_selection_raw: str = ""
    retry_selection_raw: str = ""
    selection_obj: dict[str, object] = Field(default_factory=dict)
    retry_selection_obj: dict[str, object] = Field(default_factory=dict)
    current_tool_calls: list[dict[str, object]] = Field(default_factory=list)
    tool_execution_route: str = "response"

    batch_tool_exec_inputs: list[dict[str, object]] = Field(default_factory=list)
    batch_tool_results: list[dict[str, object]] = Field(default_factory=list)
    batch_tool_failures: list[dict[str, object]] = Field(default_factory=list)
    completed_tool_results: list[dict[str, object]] = Field(default_factory=list)
    unresolved_tool_failures: list[dict[str, object]] = Field(default_factory=list)
    retry_count: int = 0
    retry_decision: str = "response"
    retry_failure_summary: str = ""
    tool_execution_summary: str = "도구 실행 없음"
    rag_references: list[dict[str, object]] = Field(default_factory=list)
    assistant_message: str = ""


# 그래프 선언
builder = StateGraph(cast(Any, ChatGraphState))

# 노드 추가
builder.add_node("safeguard", safeguard_node.run)
builder.add_node("safeguard_route", safeguard_route_node.run)
builder.add_node("tool_selector_prepare", tool_selector_prepare_node.run)
builder.add_node("tool_selector_llm", tool_selector_llm_node.arun)
builder.add_node("tool_selector_parse", tool_selector_parse_node.run)
builder.add_node("tool_selector_validate", tool_selector_validate_node.run)
builder.add_node("tool_execute_route", tool_execute_route_node.run)
builder.add_node("tool_execute_prepare", tool_execute_prepare_node.run)
builder.add_node("tool_execute_fanout_route", tool_execute_fanout_route_node.run)
builder.add_node("tool_exec", tool_exec_node.arun)
builder.add_node("tool_execute_collect", tool_execute_collect_node.run)
builder.add_node("retry_route", retry_route_node.run)
builder.add_node("retry_prepare", retry_prepare_node.run)
builder.add_node("retry_llm", retry_llm_node.arun)
builder.add_node("retry_parse", retry_parse_node.run)
builder.add_node("retry_validate", retry_validate_node.run)
builder.add_node("response_prepare", response_prepare_node.run)
builder.add_node("response_node", response_node.run)
builder.add_node("blocked", safeguard_message_node.run)

# 진입점 설정
builder.set_entry_point("safeguard")

# 엣지 설정
builder.add_edge("safeguard", "safeguard_route")
builder.add_conditional_edges(
    "safeguard_route",
    lambda state: str(state.get("safeguard_route") or "blocked"),
    {
        "response": "tool_selector_prepare",
        "blocked": "blocked",
    },
)

builder.add_edge("tool_selector_prepare", "tool_selector_llm")
builder.add_edge("tool_selector_llm", "tool_selector_parse")
builder.add_edge("tool_selector_parse", "tool_selector_validate")
builder.add_edge("tool_selector_validate", "tool_execute_route")

builder.add_conditional_edges(
    "tool_execute_route",
    lambda state: str(state.get("tool_execution_route") or "response"),
    {
        "execute": "tool_execute_prepare",
        "response": "response_prepare",
    },
)

builder.add_edge("tool_execute_prepare", "tool_execute_fanout_route")
builder.add_conditional_edges(
    "tool_execute_fanout_route",
    tool_execute_fanout_branch_node.route,
)
builder.add_edge("tool_exec", "tool_execute_collect")
builder.add_edge("tool_execute_collect", "retry_route")

builder.add_conditional_edges(
    "retry_route",
    lambda state: str(state.get("retry_decision") or "response"),
    {
        "retry": "retry_prepare",
        "response": "response_prepare",
    },
)

builder.add_edge("retry_prepare", "retry_llm")
builder.add_edge("retry_llm", "retry_parse")
builder.add_edge("retry_parse", "retry_validate")
builder.add_edge("retry_validate", "tool_execute_route")

builder.add_edge("response_prepare", "response_node")
builder.add_edge("response_node", END)
builder.add_edge("blocked", END)

# 그래프 설정 정의

# Checkpointer 정의
checkpointer = InMemorySaver()

# Stream 할 노드 정의
stream_node: StreamNodeConfig = {
    "safeguard": ["safeguard_result"],
    "safeguard_route": ["safeguard_route", "safeguard_result"],
    "tool_exec": ["tool_start", "tool_result", "tool_error"],
    "response_prepare": ["rag_references"],
    "response": ["token", "assistant_message"],
    "response_node": ["assistant_message"],
    "blocked": ["assistant_message"],
}

chat_graph = BaseChatGraph(
    builder=builder,
    checkpointer=checkpointer,
    stream_node=stream_node,
    logger=logger,
    input_model=ChatGraphInput,
)
