"""
목적: core Agent ToolExec 노드 조립체를 제공한다.
설명: 기본 ToolRegistry를 주입한 shared ToolExecNode 인스턴스를 노출한다.
디자인 패턴: 모듈 조립
참조: src/one_shot_tool_calling_agent/shared/agent/nodes/tool_exec_node.py
"""

from __future__ import annotations

from one_shot_tool_calling_agent.core.agent.tools.registry import registry
from one_shot_tool_calling_agent.shared.agent.nodes import ToolExecNode
from one_shot_tool_calling_agent.shared.logging import Logger, create_default_logger

_tool_exec_logger: Logger = create_default_logger("CoreToolExecNode")

tool_exec_node = ToolExecNode(
    registry=registry,
    node_name="tool_exec",
    tool_call_key="tool_call",
    success_key="batch_tool_results",
    failure_key="batch_tool_failures",
    logger=_tool_exec_logger,
)

__all__ = ["tool_exec_node"]
