"""
목적: Agent 그래프 공개 API를 제공한다.
설명: LangGraph 기반 1회성 Agent 그래프 엔트리를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/single_request_tool_agent/core/agent/graphs/chat_graph.py
"""

from single_request_tool_agent.core.agent.graphs.chat_graph import (
    ChatGraphInput,
    chat_graph,
)

AgentGraphInput = ChatGraphInput
agent_graph = chat_graph

__all__ = ["AgentGraphInput", "agent_graph", "ChatGraphInput", "chat_graph"]
