"""
목적: Agent 그래프 공통 추상체 공개 API를 제공한다.
설명: BaseAgentGraph를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_tool_calling_agent/shared/agent/graph/base_agent_graph.py
"""

from one_shot_tool_calling_agent.shared.agent.graph.base_agent_graph import BaseAgentGraph

__all__ = ["BaseAgentGraph"]
