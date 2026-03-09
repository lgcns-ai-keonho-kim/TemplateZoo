"""
목적: Chat 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: safeguard -> context_strategy -> schema selection -> raw SQL 생성/실행 -> response 분기 그래프를 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/text_to_sql/shared/chat/graph/base_chat_graph.py
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict

from text_to_sql.core.chat.models import ChatMessage
from text_to_sql.core.chat.nodes import (
    CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
    CONTEXT_STRATEGY_USE_METADATA,
    CONTEXT_STRATEGY_USE_SQL,
    context_strategy_finalize_node,
    context_strategy_prepare_node,
    context_strategy_route_node,
    context_strategy_node,
    execution_failure_message_node,
    metadata_answer_prepare_node,
    raw_sql_execute_node,
    raw_sql_execute_retry_node,
    raw_sql_generate_node,
    raw_sql_generate_retry_node,
    raw_sql_prepare_node,
    raw_sql_retry_prepare_node,
    response_node,
    safeguard_message_node,
    safeguard_route_node,
    safeguard_node,
    schema_selection_node,
    schema_selection_parse_node,
    schema_selection_prepare_node,
    sql_answer_prepare_node,
    sql_pipeline_failure_message_node,
    sql_result_collect_node,
)
from text_to_sql.core.chat.state import ChatGraphState
from text_to_sql.shared.chat.graph import BaseChatGraph
from text_to_sql.shared.chat.interface import StreamNodeConfig
from text_to_sql.shared.logging import Logger, create_default_logger

logger: Logger = create_default_logger("ChatGraph")


class ChatGraphInput(BaseModel):
    """그래프 실행 입력 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_message: str
    history: list[ChatMessage]
    safeguard_result: str | None = None
    safeguard_route: str | None = None
    context_strategy: str = CONTEXT_STRATEGY_USE_SQL
    context_strategy_raw: str = CONTEXT_STRATEGY_USE_SQL
    last_assistant_message: str = ""
    metadata_summary: str = ""
    sql_answer_context: str = ""
    assistant_message: str = ""


builder = StateGraph(cast(Any, ChatGraphState))
builder.add_node("safeguard", safeguard_node.run)
builder.add_node("safeguard_route", safeguard_route_node.run)
builder.add_node("context_strategy_prepare", context_strategy_prepare_node.run)
builder.add_node("context_strategy", context_strategy_node.run)
builder.add_node("context_strategy_route", context_strategy_route_node.run)
builder.add_node("context_strategy_finalize", context_strategy_finalize_node.run)
builder.add_node("metadata_answer_prepare", metadata_answer_prepare_node.run)
builder.add_node("schema_selection_prepare", schema_selection_prepare_node.run)
builder.add_node("schema_selection_llm", schema_selection_node.run)
builder.add_node("schema_selection_parse", schema_selection_parse_node.run)
builder.add_node("raw_sql_prepare", raw_sql_prepare_node.run)
builder.add_node("raw_sql_generate", raw_sql_generate_node.arun)
builder.add_node("raw_sql_execute", raw_sql_execute_node.arun)
builder.add_node("raw_sql_retry_prepare", raw_sql_retry_prepare_node.run)
builder.add_node("raw_sql_generate_retry", raw_sql_generate_retry_node.arun)
builder.add_node("raw_sql_execute_retry", raw_sql_execute_retry_node.arun)
builder.add_node("sql_result_collect", sql_result_collect_node.run)
builder.add_node("sql_answer_prepare", sql_answer_prepare_node.run)
builder.add_node("sql_pipeline_failure_message", sql_pipeline_failure_message_node.run)
builder.add_node("execution_failure_message", execution_failure_message_node.run)
builder.add_node("response", response_node.run)
builder.add_node("blocked", safeguard_message_node.run)

builder.set_entry_point("safeguard")
builder.add_edge("safeguard", "safeguard_route")
builder.add_conditional_edges(
    "safeguard_route",
    lambda state: str(state.get("safeguard_route") or "blocked"),
    {
        "response": "context_strategy_prepare",
        "blocked": "blocked",
    },
)
builder.add_edge("context_strategy_prepare", "context_strategy")
builder.add_edge("context_strategy", "context_strategy_route")
builder.add_edge("context_strategy_route", "context_strategy_finalize")
builder.add_conditional_edges(
    "context_strategy_finalize",
    lambda state: (
        "metadata_response"
        if str(state.get("context_strategy") or CONTEXT_STRATEGY_USE_SQL)
        == CONTEXT_STRATEGY_USE_METADATA
        and str(state.get("metadata_route") or "").strip().lower() == "response"
        else (
            "metadata_sql"
            if str(state.get("context_strategy") or CONTEXT_STRATEGY_USE_SQL)
            == CONTEXT_STRATEGY_USE_METADATA
            else str(state.get("context_strategy") or CONTEXT_STRATEGY_USE_SQL)
        )
    ),
    {
        CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT: "response",
        "metadata_response": "metadata_answer_prepare",
        "metadata_sql": "schema_selection_prepare",
        CONTEXT_STRATEGY_USE_SQL: "schema_selection_prepare",
    },
)
builder.add_conditional_edges(
    "metadata_answer_prepare",
    lambda state: (
        "response"
        if str(state.get("metadata_route") or "").strip().lower() == "response"
        else "sql"
    ),
    {
        "response": "response",
        "sql": "schema_selection_prepare",
    },
)
builder.add_edge("schema_selection_prepare", "schema_selection_llm")
builder.add_edge("schema_selection_llm", "schema_selection_parse")
builder.add_conditional_edges(
    "schema_selection_parse",
    lambda state: "success" if state.get("selected_target_aliases") else "failure",
    {
        "success": "raw_sql_prepare",
        "failure": "sql_pipeline_failure_message",
    },
)
builder.add_conditional_edges(
    "raw_sql_prepare",
    lambda state: "success" if state.get("raw_sql_inputs") else "failure",
    {
        "success": "raw_sql_generate",
        "failure": "sql_pipeline_failure_message",
    },
)
builder.add_conditional_edges(
    "raw_sql_generate",
    lambda state: (
        "failure"
        if state.get("sql_pipeline_failure_details")
        else ("success" if state.get("sql_texts_by_alias") else "failure")
    ),
    {
        "success": "raw_sql_execute",
        "failure": "sql_pipeline_failure_message",
    },
)
builder.add_conditional_edges(
    "raw_sql_execute",
    lambda state: "retry" if state.get("sql_retry_feedbacks") else "collect",
    {
        "retry": "raw_sql_retry_prepare",
        "collect": "sql_result_collect",
    },
)
builder.add_edge("raw_sql_retry_prepare", "raw_sql_generate_retry")
builder.add_conditional_edges(
    "raw_sql_generate_retry",
    lambda state: (
        "failure"
        if state.get("sql_pipeline_failure_details")
        else ("success" if state.get("sql_texts_by_alias") else "failure")
    ),
    {
        "success": "raw_sql_execute_retry",
        "failure": "sql_pipeline_failure_message",
    },
)
builder.add_edge("raw_sql_execute_retry", "sql_result_collect")
builder.add_conditional_edges(
    "sql_result_collect",
    lambda state: (
        "success"
        if state.get("success_aliases") and not state.get("failed_aliases")
        else "failure"
    ),
    {
        "success": "sql_answer_prepare",
        "failure": "execution_failure_message",
    },
)
builder.add_edge("sql_answer_prepare", "response")
builder.add_edge("response", END)
builder.add_edge("sql_pipeline_failure_message", END)
builder.add_edge("execution_failure_message", END)
builder.add_edge("blocked", END)

checkpointer = InMemorySaver()

stream_node: StreamNodeConfig = {
    "safeguard": ["safeguard_result"],
    "safeguard_route": ["safeguard_route", "safeguard_result"],
    "schema_selection_parse": ["sql_plan"],
    "raw_sql_generate": ["sql_plan"],
    "raw_sql_generate_retry": ["sql_plan"],
    "raw_sql_execute": ["sql_result"],
    "raw_sql_execute_retry": ["sql_result"],
    "sql_result_collect": ["sql_result"],
    "sql_pipeline_failure_message": ["assistant_message"],
    "execution_failure_message": ["assistant_message"],
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
