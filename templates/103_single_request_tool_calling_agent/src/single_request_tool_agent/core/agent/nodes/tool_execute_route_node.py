"""
목적: Tool 실행 여부 분기 노드를 제공한다.
설명: current_tool_calls 유무에 따라 execute 또는 response로 분기한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/single_request_tool_agent/core/agent/graphs/chat_graph.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from single_request_tool_agent.shared.agent.nodes import function_node
from single_request_tool_agent.shared.logging import Logger, create_default_logger

_tool_execute_route_logger: Logger = create_default_logger("ToolExecuteRouteNode")


def _run_tool_execute_route_step(state: Mapping[str, Any]) -> dict[str, Any]:
    current_tool_calls = state.get("current_tool_calls")
    has_tool_calls = bool(isinstance(current_tool_calls, list) and current_tool_calls)
    return {
        "tool_execution_route": "execute" if has_tool_calls else "response",
    }


tool_execute_route_node = function_node(
    fn=_run_tool_execute_route_step,
    node_name="tool_execute_route",
    logger=_tool_execute_route_logger,
)

__all__ = ["tool_execute_route_node"]
