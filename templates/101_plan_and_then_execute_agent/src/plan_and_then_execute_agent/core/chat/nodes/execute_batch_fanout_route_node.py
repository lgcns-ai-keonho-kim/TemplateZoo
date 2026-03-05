"""
목적: batch fan-out 라우팅 노드를 제공한다.
설명: batch_tool_exec_inputs를 기반으로 tool_exec fan-out 분기를 계산한다.
디자인 패턴: 모듈 조립
참조: src/plan_and_then_execute_agent/shared/chat/nodes/fanout_branch_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.shared.chat.nodes import FanoutBranchNode, function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_execute_batch_fanout_logger: Logger = create_default_logger("ExecuteBatchFanoutRouteNode")


def _run_execute_batch_fanout_route_step(state: Mapping[str, Any]) -> dict[str, Any]:
    del state
    # fan-out 분기는 execute_batch_fanout_branch_node.route가 담당한다.
    return {}


execute_batch_fanout_route_node = function_node(
    fn=_run_execute_batch_fanout_route_step,
    node_name="execute_batch_fanout_route",
    logger=_execute_batch_fanout_logger,
)

execute_batch_fanout_branch_node = FanoutBranchNode(
    items_key="batch_tool_exec_inputs",
    target_node="tool_exec",
    default_branch="execute_batch_collect",
    logger=_execute_batch_fanout_logger,
)

__all__ = ["execute_batch_fanout_route_node", "execute_batch_fanout_branch_node"]
