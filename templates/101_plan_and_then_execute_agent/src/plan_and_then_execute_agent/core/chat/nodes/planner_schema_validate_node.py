"""
목적: Planner 스키마 검증 노드를 제공한다.
설명: plan_obj를 표준 step 리스트로 정규화한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import normalize_plan
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_planner_schema_validate_logger: Logger = create_default_logger("PlannerSchemaValidateNode")


def _run_planner_schema_validate_step(state: Mapping[str, Any]) -> dict[str, Any]:
    plan_obj = state.get("plan_obj")
    if not isinstance(plan_obj, Mapping):
        detail = ExceptionDetail(
            code="PLAN_SCHEMA_INVALID",
            cause=f"plan_obj_type={type(plan_obj).__name__}",
        )
        raise BaseAppException("계획 객체 형식이 올바르지 않습니다.", detail)

    plan_id, steps = normalize_plan(plan_obj)
    return {
        "plan_id": plan_id,
        "plan_steps": steps,
    }


planner_schema_validate_node = function_node(
    fn=_run_planner_schema_validate_step,
    node_name="planner_schema_validate",
    logger=_planner_schema_validate_logger,
)

__all__ = ["planner_schema_validate_node"]
