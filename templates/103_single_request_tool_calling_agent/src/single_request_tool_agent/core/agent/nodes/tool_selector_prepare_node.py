"""
목적: 초기 Tool selector 입력 준비 노드를 제공한다.
설명: Tool catalog payload를 생성하고 tool 실행 누적 상태를 초기화한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/single_request_tool_agent/core/agent/tools/registry.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from single_request_tool_agent.core.agent.tools.registry import registry
from single_request_tool_agent.shared.agent.nodes import function_node
from single_request_tool_agent.shared.agent.tools import build_tool_catalog_payload
from single_request_tool_agent.shared.logging import Logger, create_default_logger

_tool_selector_prepare_logger: Logger = create_default_logger("ToolSelectorPrepareNode")


def _run_tool_selector_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    del state
    return {
        "tool_catalog_payload": build_tool_catalog_payload(registry),
        "current_tool_calls": [],
        "batch_tool_results": [],
        "batch_tool_failures": [],
        "completed_tool_results": [],
        "unresolved_tool_failures": [],
        "retry_count": 0,
        "tool_execution_summary": "도구 실행 없음",
        "retry_failure_summary": "",
    }


tool_selector_prepare_node = function_node(
    fn=_run_tool_selector_prepare_step,
    node_name="tool_selector_prepare",
    logger=_tool_selector_prepare_logger,
)

__all__ = ["tool_selector_prepare_node"]
