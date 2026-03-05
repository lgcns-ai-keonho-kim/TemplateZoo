"""
목적: Planner JSON 파싱 노드를 제공한다.
설명: planner_llm 원문(plan_raw)을 JSON 객체(plan_obj)로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import parse_plan_json
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_planner_parse_logger: Logger = create_default_logger("PlannerParseNode")


def _run_planner_parse_step(state: Mapping[str, Any]) -> dict[str, Any]:
    plan_raw = str(state.get("plan_raw") or "")
    plan_obj = parse_plan_json(plan_raw)
    return {"plan_obj": plan_obj}


planner_parse_node = function_node(
    fn=_run_planner_parse_step,
    node_name="planner_parse",
    logger=_planner_parse_logger,
)

__all__ = ["planner_parse_node"]
