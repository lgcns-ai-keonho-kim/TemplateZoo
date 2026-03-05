"""
목적: Chat 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: safeguard -> planner -> execute_queue -> response_node 흐름을 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/plan_and_then_execute_agent/shared/chat/graph/base_chat_graph.py
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from plan_and_then_execute_agent.core.chat.models import ChatMessage
from plan_and_then_execute_agent.core.chat.nodes import (
    execute_batch_collect_node,
    execute_batch_decide_node,
    execute_batch_fanout_branch_node,
    execute_batch_fanout_route_node,
    execute_batch_prepare_node,
    execute_queue_build_node,
    execute_queue_next_batch_node,
    planner_dependency_validate_node,
    planner_llm_node,
    planner_parse_node,
    planner_prepare_node,
    planner_schema_validate_node,
    planner_tools_payload_node,
    replan_llm_node,
    replan_parse_node,
    replan_prepare_node,
    replan_validate_node,
    response_node,
    response_prepare_node,
    safeguard_message_node,
    safeguard_route_node,
    safeguard_node,
    tool_exec_node,
)
from plan_and_then_execute_agent.core.chat.state import ChatGraphState
from plan_and_then_execute_agent.shared.chat.graph import BaseChatGraph
from plan_and_then_execute_agent.shared.chat.interface import StreamNodeConfig
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

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

    planner_history_summary: str = ""
    planner_tools_payload: str = ""
    available_tool_names: list[str] = Field(default_factory=list)

    plan_raw: str = ""
    replan_raw: str = ""
    plan_obj: dict[str, object] = Field(default_factory=dict)
    plan_id: str = ""
    plan_steps: list[dict[str, object]] = Field(default_factory=list)

    execute_queue: list[list[str]] = Field(default_factory=list)
    execute_decision: str = ""

    current_batch: list[str] = Field(default_factory=list)
    current_batch_started_at: float = 0.0
    batch_expected_count: int = 0
    batch_tool_exec_inputs: list[dict[str, object]] = Field(default_factory=list)
    batch_tool_results: list[dict[str, object]] = Field(default_factory=list)
    batch_tool_failures: list[dict[str, object]] = Field(default_factory=list)
    batch_failure_ids: list[str] = Field(default_factory=list)
    batch_has_failures: bool = False
    batch_elapsed_seconds: float = 0.0
    batch_timeout_exceeded: bool = False

    step_results: dict[str, dict[str, object]] = Field(default_factory=dict)
    step_failures: dict[str, dict[str, object]] = Field(default_factory=dict)

    step_timeout_seconds: float = 60.0
    replan_count: int = 0
    replan_previous_plan_summary: str = ""
    replan_failure_summary: str = ""

    plan_execution_summary: str = ""
    rag_context: str = ""
    rag_references: list[dict[str, object]] = Field(default_factory=list)
    assistant_message: str = ""


# 그래프 선언
builder = StateGraph(cast(Any, ChatGraphState))

# 노드 추가
builder.add_node("safeguard", safeguard_node.run)
builder.add_node("safeguard_route", safeguard_route_node.run)
builder.add_node("planner_prepare", planner_prepare_node.run)
builder.add_node("planner_tools_payload", planner_tools_payload_node.run)
builder.add_node("planner_llm", planner_llm_node.arun)
builder.add_node("planner_parse", planner_parse_node.run)
builder.add_node("planner_schema_validate", planner_schema_validate_node.run)
builder.add_node("planner_dependency_validate", planner_dependency_validate_node.run)
builder.add_node("execute_queue_build", execute_queue_build_node.run)
builder.add_node("execute_queue_next_batch", execute_queue_next_batch_node.run)
builder.add_node("execute_batch_prepare", execute_batch_prepare_node.run)
builder.add_node("execute_batch_fanout_route", execute_batch_fanout_route_node.run)
builder.add_node("tool_exec", tool_exec_node.arun)
builder.add_node("execute_batch_collect", execute_batch_collect_node.run)
builder.add_node("execute_batch_decide", execute_batch_decide_node.run)
builder.add_node("replan_prepare", replan_prepare_node.run)
builder.add_node("replan_llm", replan_llm_node.arun)
builder.add_node("replan_parse", replan_parse_node.run)
builder.add_node("replan_validate", replan_validate_node.run)
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
        "response": "planner_prepare",
        "blocked": "blocked",
    },
)

builder.add_edge("planner_prepare", "planner_tools_payload")
builder.add_edge("planner_tools_payload", "planner_llm")
builder.add_edge("planner_llm", "planner_parse")
builder.add_edge("planner_parse", "planner_schema_validate")
builder.add_edge("planner_schema_validate", "planner_dependency_validate")
builder.add_edge("planner_dependency_validate", "execute_queue_build")
builder.add_edge("execute_queue_build", "execute_queue_next_batch")

builder.add_conditional_edges(
    "execute_queue_next_batch",
    lambda state: str(state.get("execute_decision") or "response"),
    {
        "execute": "execute_batch_prepare",
        "response": "response_prepare",
    },
)

builder.add_edge("execute_batch_prepare", "execute_batch_fanout_route")
builder.add_conditional_edges(
    "execute_batch_fanout_route",
    execute_batch_fanout_branch_node.route,
)
builder.add_edge("tool_exec", "execute_batch_collect")
builder.add_edge("execute_batch_collect", "execute_batch_decide")

builder.add_conditional_edges(
    "execute_batch_decide",
    lambda state: str(state.get("execute_decision") or "response"),
    {
        "next_batch": "execute_queue_next_batch",
        "replan": "replan_prepare",
        "response": "response_prepare",
    },
)

builder.add_edge("replan_prepare", "replan_llm")
builder.add_edge("replan_llm", "replan_parse")
builder.add_edge("replan_parse", "replan_validate")
builder.add_edge("replan_validate", "execute_queue_build")

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
