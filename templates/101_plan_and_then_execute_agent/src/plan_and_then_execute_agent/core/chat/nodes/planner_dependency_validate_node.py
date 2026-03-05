"""
목적: Planner 의존성 검증 노드를 제공한다.
설명: plan_steps의 depends_on 무결성과 사이클 여부를 검증한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import validate_step_dependencies
from plan_and_then_execute_agent.core.chat.tools.registry import registry
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_planner_dependency_validate_logger: Logger = create_default_logger("PlannerDependencyValidateNode")


def _run_planner_dependency_validate_step(state: Mapping[str, Any]) -> dict[str, Any]:
    plan_steps = state.get("plan_steps")
    if not isinstance(plan_steps, list):
        detail = ExceptionDetail(
            code="PLAN_DEPENDENCY_INVALID",
            cause=f"plan_steps_type={type(plan_steps).__name__}",
        )
        raise BaseAppException("계획 단계 목록이 올바르지 않습니다.", detail)

    normalized = [item for item in plan_steps if isinstance(item, Mapping)]
    if len(normalized) != len(plan_steps):
        detail = ExceptionDetail(
            code="PLAN_DEPENDENCY_INVALID",
            cause="plan_steps contains non-mapping item",
        )
        raise BaseAppException("계획 단계 형식이 올바르지 않습니다.", detail)

    tool_registry = registry
    for step in normalized:
        step_id = str(step.get("id") or "").strip()
        tool_name = str(step.get("tool_name") or "").strip()
        if not tool_registry.has(tool_name):
            detail = ExceptionDetail(
                code="PLAN_TOOL_UNKNOWN",
                cause=f"step_id={step_id}, tool_name={tool_name}",
                hint="planner는 ToolRegistry에 등록된 tool_name만 선택해야 합니다.",
            )
            raise BaseAppException("계획 단계의 tool_name이 등록되지 않았습니다.", detail)

    validate_step_dependencies(normalized)
    return {"plan_steps": [dict(item) for item in normalized]}


planner_dependency_validate_node = function_node(
    fn=_run_planner_dependency_validate_step,
    node_name="planner_dependency_validate",
    logger=_planner_dependency_validate_logger,
)

__all__ = ["planner_dependency_validate_node"]
