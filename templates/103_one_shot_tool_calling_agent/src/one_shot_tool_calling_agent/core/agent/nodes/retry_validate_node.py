"""
목적: Tool retry 결과 검증 노드를 제공한다.
설명: retry_selection_obj를 ToolRegistry 기준으로 검증하고 재실행 가능한 ToolCall 목록으로 정규화한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/one_shot_tool_calling_agent/core/agent/nodes/_tool_call_selection.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from one_shot_tool_calling_agent.core.agent.nodes._tool_call_selection import (
    build_tool_calls,
)
from one_shot_tool_calling_agent.core.agent.tools.registry import registry
from one_shot_tool_calling_agent.shared.agent.nodes import function_node
from one_shot_tool_calling_agent.shared.logging import Logger, create_default_logger

_retry_validate_logger: Logger = create_default_logger("RetryValidateNode")


def _run_retry_validate_step(state: Mapping[str, Any]) -> dict[str, Any]:
    retry_selection_obj = state.get("retry_selection_obj")
    raw_unresolved_failures = state.get("unresolved_tool_failures")
    unresolved_failures = (
        [dict(item) for item in raw_unresolved_failures if isinstance(item, Mapping)]
        if isinstance(raw_unresolved_failures, list)
        else []
    )
    failure_ids = [
        str(item.get("tool_call_id") or "")
        for item in unresolved_failures
        if str(item.get("tool_call_id") or "").strip()
    ]
    payload = (
        dict(retry_selection_obj) if isinstance(retry_selection_obj, Mapping) else {}
    )
    current_tool_calls = build_tool_calls(
        payload=payload,
        registry=registry,
        session_id=str(state.get("session_id") or ""),
        request_id=str(state.get("request_id") or ""),
        state=state,
        allow_retry_for=True,
        known_failure_ids=failure_ids,
    )
    return {"current_tool_calls": current_tool_calls}


retry_validate_node = function_node(
    fn=_run_retry_validate_step,
    node_name="retry_validate",
    logger=_retry_validate_logger,
)

__all__ = ["retry_validate_node"]
