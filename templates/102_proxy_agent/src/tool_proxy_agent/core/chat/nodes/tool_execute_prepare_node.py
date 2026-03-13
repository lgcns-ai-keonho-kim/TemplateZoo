"""
목적: Tool batch 실행 입력 준비 노드를 제공한다.
설명: current_tool_calls를 ToolExec fan-out 입력으로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/tool_proxy_agent/shared/chat/nodes/fanout_branch_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tool_proxy_agent.shared.chat.nodes import function_node
from tool_proxy_agent.shared.logging import Logger, create_default_logger

_tool_execute_prepare_logger: Logger = create_default_logger("ToolExecutePrepareNode")


def _run_tool_execute_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    raw_tool_calls = state.get("current_tool_calls")
    tool_calls = (
        [dict(item) for item in raw_tool_calls if isinstance(item, Mapping)]
        if isinstance(raw_tool_calls, list)
        else []
    )
    return {
        "batch_tool_exec_inputs": [{"tool_call": item} for item in tool_calls],
        "batch_tool_results": [],
        "batch_tool_failures": [],
    }


tool_execute_prepare_node = function_node(
    fn=_run_tool_execute_prepare_step,
    node_name="tool_execute_prepare",
    logger=_tool_execute_prepare_logger,
)

__all__ = ["tool_execute_prepare_node"]
