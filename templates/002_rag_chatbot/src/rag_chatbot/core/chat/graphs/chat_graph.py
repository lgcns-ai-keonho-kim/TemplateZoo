"""
목적: Chat 그래프 조립과 기본 싱글턴 인스턴스를 제공한다.
설명: safeguard -> rag 단계 노드 -> response / blocked 분기 그래프를 모듈 레벨에서 조립한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/rag_chatbot/shared/chat/graph/base_chat_graph.py
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from rag_chatbot.core.chat.models import ChatMessage
from rag_chatbot.core.chat.nodes import (
    CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
    CONTEXT_STRATEGY_USE_RAG,
    context_strategy_finalize_node,
    context_strategy_prepare_node,
    context_strategy_route_node,
    context_strategy_node,
    rag_chunk_dedup_node,
    rag_file_page_dedup_node,
    rag_format_node,
    rag_final_topk_node,
    rag_keyword_llm_node,
    rag_keyword_postprocess_node,
    rag_relevance_collect_node,
    rag_relevance_judge_node,
    rag_relevance_prepare_node,
    rag_retrieve_node,
    response_node,
    safeguard_message_node,
    safeguard_route_node,
    safeguard_node,
)
from rag_chatbot.core.chat.state import ChatGraphState
from rag_chatbot.shared.chat.graph import BaseChatGraph
from rag_chatbot.shared.chat.interface import StreamNodeConfig
from rag_chatbot.shared.chat.nodes import FanoutBranchNode
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
    context_strategy: str = CONTEXT_STRATEGY_USE_RAG
    context_strategy_raw: str = CONTEXT_STRATEGY_USE_RAG
    last_assistant_message: str = ""
    rag_context: str = ""
    rag_references: list[dict[str, object]] = Field(default_factory=list)
    assistant_message: str = ""


rag_relevance_fanout_branch_node = FanoutBranchNode(
    items_key="rag_relevance_judge_inputs",
    target_node="rag_relevance_judge",
    default_branch="rag_relevance_collect",
)


# 그래프 선언
builder = StateGraph(cast(Any, ChatGraphState))
# 노드 추가
builder.add_node("safeguard", safeguard_node.run)
builder.add_node("safeguard_route", safeguard_route_node.run)
builder.add_node("context_strategy_prepare", context_strategy_prepare_node.run)
builder.add_node("context_strategy", context_strategy_node.run)
builder.add_node("context_strategy_route", context_strategy_route_node.run)
builder.add_node("context_strategy_finalize", context_strategy_finalize_node.run)
builder.add_node("rag_keyword_llm", rag_keyword_llm_node.arun)
builder.add_node("rag_keyword_postprocess", rag_keyword_postprocess_node.arun)
builder.add_node("rag_retrieve", rag_retrieve_node.arun)
builder.add_node("rag_chunk_dedup", rag_chunk_dedup_node.arun)
builder.add_node("rag_relevance_prepare", rag_relevance_prepare_node.arun)
builder.add_node("rag_relevance_judge", rag_relevance_judge_node.arun)
builder.add_node("rag_relevance_collect", rag_relevance_collect_node.arun)
builder.add_node("rag_file_page_dedup", rag_file_page_dedup_node.arun)
builder.add_node("rag_final_topk", rag_final_topk_node.arun)
builder.add_node("rag_format", rag_format_node.arun)
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
        "response": "context_strategy_prepare",
        "blocked": "blocked",
    },
)
builder.add_edge("context_strategy_prepare", "context_strategy")
builder.add_edge("context_strategy", "context_strategy_route")
builder.add_edge("context_strategy_route", "context_strategy_finalize")
builder.add_conditional_edges(
    "context_strategy_finalize",
    lambda state: str(state.get("context_strategy") or CONTEXT_STRATEGY_USE_RAG),
    {
        CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT: "response",
        CONTEXT_STRATEGY_USE_RAG: "rag_keyword_llm",
    },
)
builder.add_edge("rag_keyword_llm", "rag_keyword_postprocess")
builder.add_edge("rag_keyword_postprocess", "rag_retrieve")
builder.add_edge("rag_retrieve", "rag_chunk_dedup")
builder.add_edge("rag_chunk_dedup", "rag_relevance_prepare")
builder.add_conditional_edges(
    "rag_relevance_prepare",
    rag_relevance_fanout_branch_node.route,
)
builder.add_edge("rag_relevance_judge", "rag_relevance_collect")
builder.add_edge("rag_relevance_collect", "rag_file_page_dedup")
builder.add_edge("rag_file_page_dedup", "rag_final_topk")
builder.add_edge("rag_final_topk", "rag_format")
builder.add_edge("rag_format", "response")
builder.add_edge("response", END)
builder.add_edge("blocked", END)

# 그래프 설정 정의

# Checkpointer 정의
checkpointer = InMemorySaver()

# Stream 할 노드 정의
stream_node: StreamNodeConfig = {
    "safeguard": ["safeguard_result"],
    "safeguard_route": ["safeguard_route", "safeguard_result"],
    "rag_format": ["rag_context", "rag_references"],
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
