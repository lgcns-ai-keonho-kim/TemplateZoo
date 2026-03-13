"""
목적: Tool selector 결과 검증 노드를 제공한다.
설명: selection_obj를 ToolRegistry 기준으로 검증하고 실행 가능한 ToolCall 목록으로 정규화한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/tool_proxy_agent/core/chat/nodes/_tool_call_selection.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tool_proxy_agent.core.chat.nodes._tool_call_selection import (
    build_tool_calls,
)
from tool_proxy_agent.core.chat.tools.registry import registry
from tool_proxy_agent.shared.chat.nodes import function_node
from tool_proxy_agent.shared.logging import Logger, create_default_logger

_tool_selector_validate_logger: Logger = create_default_logger(
    "ToolSelectorValidateNode"
)


def _run_tool_selector_validate_step(state: Mapping[str, Any]) -> dict[str, Any]:
    selection_obj = state.get("selection_obj")
    payload = dict(selection_obj) if isinstance(selection_obj, Mapping) else {}
    current_tool_calls = build_tool_calls(
        payload=payload,
        registry=registry,
        session_id=str(state.get("session_id") or ""),
        request_id=str(state.get("request_id") or ""),
        state=state,
        allow_retry_for=False,
    )
    return {"current_tool_calls": current_tool_calls}


tool_selector_validate_node = function_node(
    fn=_run_tool_selector_validate_step,
    node_name="tool_selector_validate",
    logger=_tool_selector_validate_logger,
)

__all__ = ["tool_selector_validate_node"]
