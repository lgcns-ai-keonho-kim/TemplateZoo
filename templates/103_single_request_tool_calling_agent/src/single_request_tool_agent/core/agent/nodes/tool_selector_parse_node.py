"""
목적: Tool selector JSON 파싱 노드를 제공한다.
설명: tool_selector_llm 원문(tool_selection_raw)을 JSON 객체(selection_obj)로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/single_request_tool_agent/core/agent/nodes/_tool_call_selection.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from single_request_tool_agent.core.agent.nodes._tool_call_selection import (
    parse_tool_call_json,
)
from single_request_tool_agent.shared.agent.nodes import function_node
from single_request_tool_agent.shared.logging import Logger, create_default_logger

_tool_selector_parse_logger: Logger = create_default_logger("ToolSelectorParseNode")


def _run_tool_selector_parse_step(state: Mapping[str, Any]) -> dict[str, Any]:
    tool_selection_raw = str(state.get("tool_selection_raw") or "")
    selection_obj = parse_tool_call_json(tool_selection_raw, label="Tool selector")
    return {"selection_obj": selection_obj}


tool_selector_parse_node = function_node(
    fn=_run_tool_selector_parse_step,
    node_name="tool_selector_parse",
    logger=_tool_selector_parse_logger,
)

__all__ = ["tool_selector_parse_node"]
