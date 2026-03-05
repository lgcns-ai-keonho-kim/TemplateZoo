"""
목적: Replan JSON 파싱 노드를 제공한다.
설명: replan_llm 원문(replan_raw)을 JSON 객체로 파싱한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import parse_plan_json
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_replan_parse_logger: Logger = create_default_logger("ReplanParseNode")


def _run_replan_parse_step(state: Mapping[str, Any]) -> dict[str, Any]:
    replan_raw = str(state.get("replan_raw") or "")
    plan_obj = parse_plan_json(replan_raw)
    return {"plan_obj": plan_obj}


replan_parse_node = function_node(
    fn=_run_replan_parse_step,
    node_name="replan_parse",
    logger=_replan_parse_logger,
)

__all__ = ["replan_parse_node"]
