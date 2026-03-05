"""
목적: batch 실행 결과 수집 노드를 제공한다.
설명: fan-out ToolExec 결과를 step_results/step_failures로 병합하고 timeout을 판정한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/execute_batch_decide_node.py
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_execute_batch_collect_logger: Logger = create_default_logger("ExecuteBatchCollectNode")
_STEP_TIMEOUT_SECONDS_DEFAULT = 60.0


def _as_mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _run_execute_batch_collect_step(state: Mapping[str, Any]) -> dict[str, Any]:
    current_batch = state.get("current_batch")
    current_batch_ids = [str(item).strip() for item in current_batch if str(item).strip()] if isinstance(current_batch, list) else []

    batch_results = _as_mapping_list(state.get("batch_tool_results"))
    batch_failures = _as_mapping_list(state.get("batch_tool_failures"))

    step_results = dict(state.get("step_results") or {}) if isinstance(state.get("step_results"), Mapping) else {}
    step_failures = dict(state.get("step_failures") or {}) if isinstance(state.get("step_failures"), Mapping) else {}

    observed_step_ids: set[str] = set()

    for item in batch_results:
        step_id = str(item.get("step_id") or "").strip()
        if not step_id:
            continue
        observed_step_ids.add(step_id)
        item["ok"] = True
        step_results[step_id] = item
        step_failures.pop(step_id, None)

    for item in batch_failures:
        step_id = str(item.get("step_id") or "").strip()
        if not step_id:
            continue
        observed_step_ids.add(step_id)
        item["ok"] = False
        step_failures[step_id] = item
        step_results.pop(step_id, None)

    step_timeout_seconds = max(float(state.get("step_timeout_seconds") or _STEP_TIMEOUT_SECONDS_DEFAULT), 0.001)
    started_at = float(state.get("current_batch_started_at") or 0.0)
    elapsed_seconds = max(time.monotonic() - started_at, 0.0) if started_at > 0 else 0.0
    timeout_exceeded = bool(started_at > 0 and elapsed_seconds > step_timeout_seconds)

    if timeout_exceeded:
        timeout_error = (
            f"step timeout exceeded ({step_timeout_seconds:.1f}s), "
            f"elapsed={elapsed_seconds:.1f}s"
        )
        for step_id in current_batch_ids:
            timeout_failure = {
                "step_id": step_id,
                "tool_name": "",
                "ok": False,
                "output": {},
                "error": timeout_error,
                "error_code": "STEP_TIMEOUT",
                "attempt": 1,
                "duration_ms": int(elapsed_seconds * 1000),
                "plan_id": str(state.get("plan_id") or ""),
            }
            step_failures[step_id] = timeout_failure
            step_results.pop(step_id, None)

    for step_id in current_batch_ids:
        if step_id in observed_step_ids:
            continue
        if step_id in step_failures:
            continue
        missing_failure = {
            "step_id": step_id,
            "tool_name": "",
            "ok": False,
            "output": {},
            "error": "step result missing",
            "error_code": "STEP_RESULT_MISSING",
            "attempt": 1,
            "duration_ms": int(elapsed_seconds * 1000),
            "plan_id": str(state.get("plan_id") or ""),
        }
        step_failures[step_id] = missing_failure
        step_results.pop(step_id, None)

    batch_failure_ids = [step_id for step_id in current_batch_ids if step_id in step_failures]

    return {
        "step_results": step_results,
        "step_failures": step_failures,
        "batch_failure_ids": batch_failure_ids,
        "batch_has_failures": bool(batch_failure_ids),
        "batch_elapsed_seconds": elapsed_seconds,
        "batch_timeout_exceeded": timeout_exceeded,
    }


execute_batch_collect_node = function_node(
    fn=_run_execute_batch_collect_step,
    node_name="execute_batch_collect",
    logger=_execute_batch_collect_logger,
)

__all__ = ["execute_batch_collect_node"]
