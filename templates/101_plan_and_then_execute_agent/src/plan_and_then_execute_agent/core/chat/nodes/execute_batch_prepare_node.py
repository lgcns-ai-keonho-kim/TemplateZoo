"""
목적: batch 실행 입력 준비 노드를 제공한다.
설명: current_batch step id 목록을 ToolCall fan-out 입력 목록으로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/shared/chat/nodes/fanout_branch_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_execute_batch_prepare_logger: Logger = create_default_logger("ExecuteBatchPrepareNode")


def _run_execute_batch_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    current_batch = state.get("current_batch")
    plan_steps = state.get("plan_steps")

    batch_step_ids = [str(item).strip() for item in current_batch if str(item).strip()] if isinstance(current_batch, list) else []
    step_map: dict[str, dict[str, Any]] = {}
    if isinstance(plan_steps, list):
        for step in plan_steps:
            if not isinstance(step, Mapping):
                continue
            step_id = str(step.get("id") or "").strip()
            if not step_id:
                continue
            step_map[step_id] = dict(step)

    session_id = str(state.get("session_id") or "")
    request_id = str(state.get("request_id") or "")
    plan_id = str(state.get("plan_id") or "")

    inputs: list[dict[str, Any]] = []
    for index, step_id in enumerate(batch_step_ids):
        step = step_map.get(step_id)
        if not step:
            continue
        inputs.append(
            {
                "tool_call": {
                    "tool_name": str(step.get("tool_name") or "").strip(),
                    "args": dict(step.get("args") or {}) if isinstance(step.get("args"), Mapping) else {},
                    "session_id": session_id,
                    "request_id": request_id,
                    "plan_id": plan_id,
                    "step_id": step_id,
                    "step_index": index,
                }
            }
        )

    return {
        "batch_tool_exec_inputs": inputs,
        "batch_expected_count": len(inputs),
        "batch_tool_results": [],
        "batch_tool_failures": [],
    }


execute_batch_prepare_node = function_node(
    fn=_run_execute_batch_prepare_step,
    node_name="execute_batch_prepare",
    logger=_execute_batch_prepare_logger,
)

__all__ = ["execute_batch_prepare_node"]
