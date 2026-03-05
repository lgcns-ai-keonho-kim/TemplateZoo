"""
목적: Replan 검증 노드를 제공한다.
설명: 파싱된 replan 객체를 표준 step 리스트로 정규화하고 의존성을 검증한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import normalize_plan, validate_step_dependencies
from plan_and_then_execute_agent.core.chat.tools.registry import registry
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_replan_validate_logger: Logger = create_default_logger("ReplanValidateNode")


def _run_replan_validate_step(state: Mapping[str, Any]) -> dict[str, Any]:
    plan_obj = state.get("plan_obj")
    if not isinstance(plan_obj, Mapping):
        detail = ExceptionDetail(
            code="REPLAN_SCHEMA_INVALID",
            cause=f"plan_obj_type={type(plan_obj).__name__}",
        )
        raise BaseAppException("재계획 객체 형식이 올바르지 않습니다.", detail)

    plan_id, steps = normalize_plan(plan_obj)
    tool_registry = registry
    for step in steps:
        step_id = str(step.get("id") or "").strip()
        tool_name = str(step.get("tool_name") or "").strip()
        if not tool_registry.has(tool_name):
            detail = ExceptionDetail(
                code="REPLAN_TOOL_UNKNOWN",
                cause=f"step_id={step_id}, tool_name={tool_name}",
                hint="replanner는 ToolRegistry에 등록된 tool_name만 선택해야 합니다.",
            )
            raise BaseAppException("재계획 단계의 tool_name이 등록되지 않았습니다.", detail)
    validate_step_dependencies(steps)

    return {
        "plan_id": plan_id,
        "plan_steps": steps,
    }


replan_validate_node = function_node(
    fn=_run_replan_validate_step,
    node_name="replan_validate",
    logger=_replan_validate_logger,
)

__all__ = ["replan_validate_node"]
