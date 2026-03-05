"""
목적: 실행 큐 생성 노드를 제공한다.
설명: plan_steps를 의존성 레벨(batch) 단위 execute_queue로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import build_execute_queue_levels
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_execute_queue_build_logger: Logger = create_default_logger("ExecuteQueueBuildNode")


def _run_execute_queue_build_step(state: Mapping[str, Any]) -> dict[str, Any]:
    plan_steps = state.get("plan_steps")
    if not isinstance(plan_steps, list):
        detail = ExceptionDetail(
            code="EXECUTE_QUEUE_BUILD_INVALID",
            cause=f"plan_steps_type={type(plan_steps).__name__}",
        )
        raise BaseAppException("실행 큐 생성을 위한 계획 단계가 올바르지 않습니다.", detail)

    normalized_steps = [dict(item) for item in plan_steps if isinstance(item, Mapping)]
    if len(normalized_steps) != len(plan_steps):
        detail = ExceptionDetail(
            code="EXECUTE_QUEUE_BUILD_INVALID",
            cause="plan_steps contains non-mapping item",
        )
        raise BaseAppException("실행 큐 생성을 위한 계획 단계가 올바르지 않습니다.", detail)

    execute_queue = build_execute_queue_levels(normalized_steps)
    step_results = state.get("step_results")

    return {
        "plan_steps": normalized_steps,
        "execute_queue": execute_queue,
        "current_batch": [],
        "batch_expected_count": 0,
        "batch_tool_exec_inputs": [],
        "batch_tool_results": [],
        "batch_tool_failures": [],
        "step_results": dict(step_results) if isinstance(step_results, Mapping) else {},
        "step_failures": {},
    }


execute_queue_build_node = function_node(
    fn=_run_execute_queue_build_step,
    node_name="execute_queue_build",
    logger=_execute_queue_build_logger,
)

__all__ = ["execute_queue_build_node"]
