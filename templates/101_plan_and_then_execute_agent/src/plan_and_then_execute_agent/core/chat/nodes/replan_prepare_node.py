"""
목적: Replan 입력 준비 노드를 제공한다.
설명: 이전 계획/실패 요약을 생성하고 replan_count를 증가시킨다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/replan_llm_node.py
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.tools.registry import registry
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.chat.tools import build_planner_tools_payload
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_replan_prepare_logger: Logger = create_default_logger("ReplanPrepareNode")


def _summarize_previous_plan(plan_id: str, plan_steps: list[dict[str, Any]]) -> str:
    payload = {
        "plan_id": plan_id,
        "steps": [
            {
                "id": str(step.get("id") or ""),
                "goal": str(step.get("goal") or ""),
                "tool_name": str(step.get("tool_name") or ""),
                "depends_on": list(step.get("depends_on") or []) if isinstance(step.get("depends_on"), list) else [],
            }
            for step in plan_steps
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _summarize_failures(step_failures: Mapping[str, Any]) -> str:
    if not step_failures:
        return "no failures"

    lines: list[str] = []
    for step_id, raw in step_failures.items():
        if isinstance(raw, Mapping):
            error_code = str(raw.get("error_code") or "")
            error_message = str(raw.get("error") or "failed")
            tool_name = str(raw.get("tool_name") or "")
        else:
            error_code = ""
            error_message = str(raw)
            tool_name = ""
        lines.append(
            f"- step_id={step_id}, tool_name={tool_name}, error_code={error_code}, error={error_message}"
        )
    return "\n".join(lines)


def _run_replan_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    plan_id = str(state.get("plan_id") or "")
    plan_steps_raw = state.get("plan_steps")
    plan_steps = [dict(item) for item in plan_steps_raw if isinstance(item, Mapping)] if isinstance(plan_steps_raw, list) else []

    failures_raw = state.get("step_failures")
    step_failures = dict(failures_raw) if isinstance(failures_raw, Mapping) else {}

    tools_payload = state.get("planner_tools_payload")
    if not isinstance(tools_payload, str) or not tools_payload.strip():
        tools_payload = build_planner_tools_payload(registry)

    next_replan_count = int(state.get("replan_count") or 0) + 1

    return {
        "replan_previous_plan_summary": _summarize_previous_plan(plan_id, plan_steps),
        "replan_failure_summary": _summarize_failures(step_failures),
        "replan_count": next_replan_count,
        "planner_tools_payload": tools_payload,
    }


replan_prepare_node = function_node(
    fn=_run_replan_prepare_step,
    node_name="replan_prepare",
    logger=_replan_prepare_logger,
)

__all__ = ["replan_prepare_node"]
