"""
목적: Tool batch 실행 결과 수집 노드를 제공한다.
설명: batch ToolExec 결과를 누적 성공/미해결 실패 목록으로 병합한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/single_request_tool_agent/core/agent/nodes/retry_route_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from single_request_tool_agent.shared.agent.nodes import function_node
from single_request_tool_agent.shared.logging import Logger, create_default_logger

_tool_execute_collect_logger: Logger = create_default_logger("ToolExecuteCollectNode")


def _as_mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _resolve_failure_identity(item: Mapping[str, Any]) -> str:
    retry_for = str(item.get("retry_for") or "").strip()
    if retry_for:
        return retry_for
    return str(item.get("tool_call_id") or "").strip()


def _run_tool_execute_collect_step(state: Mapping[str, Any]) -> dict[str, Any]:
    previous_completed = _as_mapping_list(state.get("completed_tool_results"))
    previous_failures = _as_mapping_list(state.get("unresolved_tool_failures"))
    batch_results = _as_mapping_list(state.get("batch_tool_results"))
    batch_failures = _as_mapping_list(state.get("batch_tool_failures"))

    completed_by_call_id = {
        str(item.get("tool_call_id") or ""): item
        for item in previous_completed
        if str(item.get("tool_call_id") or "").strip()
    }
    unresolved_by_identity = {
        _resolve_failure_identity(item): item
        for item in previous_failures
        if _resolve_failure_identity(item)
    }

    for item in batch_results:
        tool_call_id = str(item.get("tool_call_id") or "").strip()
        if tool_call_id:
            completed_by_call_id[tool_call_id] = item
        identity = _resolve_failure_identity(item)
        if identity:
            unresolved_by_identity.pop(identity, None)

    for item in batch_failures:
        identity = _resolve_failure_identity(item)
        if identity:
            unresolved_by_identity[identity] = item

    return {
        "completed_tool_results": list(completed_by_call_id.values()),
        "unresolved_tool_failures": list(unresolved_by_identity.values()),
    }


tool_execute_collect_node = function_node(
    fn=_run_tool_execute_collect_step,
    node_name="tool_execute_collect",
    logger=_tool_execute_collect_logger,
)

__all__ = ["tool_execute_collect_node"]
