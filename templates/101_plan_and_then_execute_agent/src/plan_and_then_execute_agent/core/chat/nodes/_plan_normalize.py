"""
목적: Planner steps 정규화 유틸을 제공한다.
설명: plan 객체를 표준 실행 단계 형태로 변환한다.
디자인 패턴: 유틸리티
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail


def normalize_plan(plan_obj: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """계획 객체를 실행 가능한 표준 steps 리스트로 정규화한다."""

    plan_id = str(plan_obj.get("plan_id") or "").strip() or str(uuid4())
    raw_steps = plan_obj.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        detail = ExceptionDetail(code="PLAN_STEPS_EMPTY", cause="steps is missing or empty")
        raise BaseAppException("계획 단계(steps)가 비어 있습니다.", detail)

    normalized_steps: list[dict[str, Any]] = []
    for index, raw_step in enumerate(raw_steps, start=1):
        if not isinstance(raw_step, Mapping):
            detail = ExceptionDetail(
                code="PLAN_STEP_INVALID",
                cause=f"index={index}, step_type={type(raw_step).__name__}",
            )
            raise BaseAppException("계획 단계 형식이 올바르지 않습니다.", detail)

        step_id = str(raw_step.get("id") or "").strip() or f"step_{index}"
        goal = str(raw_step.get("goal") or "").strip() or step_id
        tool_name = str(raw_step.get("tool_name") or "").strip()
        if not tool_name:
            detail = ExceptionDetail(
                code="PLAN_STEP_TOOL_MISSING",
                cause=f"step_id={step_id}",
            )
            raise BaseAppException("계획 단계에 tool_name이 없습니다.", detail)

        args_raw = raw_step.get("args")
        args = dict(args_raw) if isinstance(args_raw, Mapping) else {}

        depends_on_raw = raw_step.get("depends_on")
        depends_on: list[str] = []
        if isinstance(depends_on_raw, list):
            depends_on = [
                str(item).strip()
                for item in depends_on_raw
                if str(item).strip()
            ]

        normalized_steps.append(
            {
                "id": step_id,
                "goal": goal,
                "tool_name": tool_name,
                "args": args,
                "depends_on": depends_on,
            }
        )

    return plan_id, normalized_steps

