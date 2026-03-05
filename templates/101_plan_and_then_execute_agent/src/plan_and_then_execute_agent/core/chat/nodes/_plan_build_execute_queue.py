"""
목적: Planner 단계 실행 큐 빌더 유틸을 제공한다.
설명: 의존성을 기반으로 병렬 실행 가능한 레벨 큐를 생성한다.
디자인 패턴: 유틸리티
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_validate_dependencies.py
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_validate_dependencies import (
    validate_step_dependencies,
)
from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail


def build_execute_queue_levels(steps: Sequence[Mapping[str, Any]]) -> list[list[str]]:
    """steps를 의존성 레벨(batch) 단위 실행 큐로 변환한다."""

    validate_step_dependencies(steps)

    step_ids: list[str] = [str(step.get("id") or "").strip() for step in steps]
    order_index = {step_id: index for index, step_id in enumerate(step_ids)}

    indegree: dict[str, int] = {step_id: 0 for step_id in step_ids}
    graph: dict[str, list[str]] = defaultdict(list)
    for step in steps:
        step_id = str(step.get("id") or "").strip()
        dependencies = _to_dependency_list(step)
        for dependency in dependencies:
            dep_id = str(dependency or "").strip()
            graph[dep_id].append(step_id)
            indegree[step_id] += 1

    ready: list[str] = [step_id for step_id in step_ids if indegree[step_id] == 0]
    ready.sort(key=lambda item: order_index[item])

    levels: list[list[str]] = []
    visited = 0
    while ready:
        current_level = ready
        levels.append(current_level)
        visited += len(current_level)

        next_ready: list[str] = []
        for current in current_level:
            for nxt in graph.get(current, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    next_ready.append(nxt)

        next_ready.sort(key=lambda item: order_index[item])
        ready = next_ready

    if visited != len(step_ids):
        detail = ExceptionDetail(
            code="PLAN_DEPENDENCY_CYCLE",
            cause="cycle detected while building execute queue",
        )
        raise BaseAppException("실행 큐 생성 중 순환 의존성이 감지되었습니다.", detail)

    return levels


def _to_dependency_list(step: Mapping[str, Any]) -> list[Any]:
    raw_dependencies = step.get("depends_on")
    dependencies: list[Any] = []
    if not isinstance(raw_dependencies, list):
        return dependencies
    for dependency in raw_dependencies:
        dependencies.append(dependency)
    return dependencies

