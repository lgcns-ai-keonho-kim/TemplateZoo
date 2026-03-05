"""
목적: Planner Tool 스펙 payload 생성 노드를 제공한다.
설명: ToolRegistry에서 planner 프롬프트 주입용 JSON payload를 만든다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/tools/__init__.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.tools.registry import registry
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.chat.tools import build_planner_tools_payload
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_planner_tools_payload_logger: Logger = create_default_logger("PlannerToolsPayloadNode")


def _run_planner_tools_payload_step(state: Mapping[str, Any]) -> dict[str, Any]:
    del state
    payload = build_planner_tools_payload(registry)
    tools = registry.get_tools()
    return {
        "planner_tools_payload": payload,
        "available_tool_names": [spec.name for spec in tools],
    }


planner_tools_payload_node = function_node(
    fn=_run_planner_tools_payload_step,
    node_name="planner_tools_payload",
    logger=_planner_tools_payload_logger,
)

__all__ = ["planner_tools_payload_node"]
