"""
목적: Tool retry JSON 파싱 노드를 제공한다.
설명: retry_llm 원문(retry_selection_raw)을 JSON 객체(retry_selection_obj)로 변환한다.
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

_retry_parse_logger: Logger = create_default_logger("RetryParseNode")


def _run_retry_parse_step(state: Mapping[str, Any]) -> dict[str, Any]:
    retry_selection_raw = str(state.get("retry_selection_raw") or "")
    retry_selection_obj = parse_tool_call_json(
        retry_selection_raw, label="Retry selector"
    )
    return {"retry_selection_obj": retry_selection_obj}


retry_parse_node = function_node(
    fn=_run_retry_parse_step,
    node_name="retry_parse",
    logger=_retry_parse_logger,
)

__all__ = ["retry_parse_node"]
