"""
목적: Planner 입력 준비 노드를 제공한다.
설명: 대화 히스토리를 요약해 planner_llm 입력 키를 세팅한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/planner_llm_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import summarize_history
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_planner_prepare_logger: Logger = create_default_logger("PlannerPrepareNode")


def _run_planner_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    history = state.get("history")
    history_items = history if isinstance(history, list) else []
    summary = summarize_history(history_items, limit=6)

    step_results = state.get("step_results")
    step_failures = state.get("step_failures")

    return {
        "planner_history_summary": summary,
        "step_results": dict(step_results) if isinstance(step_results, Mapping) else {},
        "step_failures": dict(step_failures) if isinstance(step_failures, Mapping) else {},
        "replan_count": int(state.get("replan_count") or 0),
    }


planner_prepare_node = function_node(
    fn=_run_planner_prepare_step,
    node_name="planner_prepare",
    logger=_planner_prepare_logger,
)

__all__ = ["planner_prepare_node"]
