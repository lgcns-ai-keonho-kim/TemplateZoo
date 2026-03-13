"""
목적: Agent 그래프 공통 추상체 공개 API를 제공한다.
설명: BaseChatGraph를 Agent 공용 래퍼로 재사용할 수 있도록 노출한다.
디자인 패턴: 퍼사드
참조: src/single_request_tool_agent/shared/agent/graph/base_chat_graph.py
"""

from single_request_tool_agent.shared.agent.graph.base_chat_graph import BaseChatGraph

BaseAgentGraph = BaseChatGraph

__all__ = ["BaseAgentGraph", "BaseChatGraph"]
