"""
목적: Planner 단계 의존성 검증 유틸을 제공한다.
설명: 단계 ID 중복/미존재/자기참조/사이클을 검증한다.
디자인 패턴: 유틸리티
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from typing import Any

from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail


def validate_step_dependencies(steps: Sequence[Mapping[str, Any]]) -> None:
    """steps 의존성 무결성/사이클 여부를 검증한다."""

    step_ids: list[str] = [str(step.get("id") or "").strip() for step in steps]
    if any(not item for item in step_ids):
        detail = ExceptionDetail(code="PLAN_STEP_ID_INVALID", cause="empty step id exists")
        raise BaseAppException("계획 단계 ID가 올바르지 않습니다.", detail)

    duplicated = _find_duplicates(step_ids)
    if duplicated:
        detail = ExceptionDetail(
            code="PLAN_STEP_ID_DUPLICATED",
            cause=f"duplicated={','.join(duplicated)}",
        )
        raise BaseAppException("중복된 단계 ID가 있습니다.", detail)

    step_id_set = set(step_ids)
    for step in steps:
        step_id = str(step.get("id") or "").strip()
        dependencies = _to_dependency_list(step)
        for dependency in dependencies:
            dep_id = str(dependency or "").strip()
            if not dep_id:
                continue
            if dep_id == step_id:
                detail = ExceptionDetail(
                    code="PLAN_DEPENDENCY_SELF",
                    cause=f"step_id={step_id}",
                )
                raise BaseAppException("자기 자신을 의존하는 단계가 있습니다.", detail)
            if dep_id not in step_id_set:
                detail = ExceptionDetail(
                    code="PLAN_DEPENDENCY_UNKNOWN",
                    cause=f"step_id={step_id}, depends_on={dep_id}",
                )
                raise BaseAppException("존재하지 않는 의존 단계가 있습니다.", detail)

    # 사이클 검증(Kahn)
    indegree: dict[str, int] = {step_id: 0 for step_id in step_ids}
    graph: dict[str, list[str]] = defaultdict(list)
    for step in steps:
        step_id = str(step.get("id") or "").strip()
        dependencies = _to_dependency_list(step)
        for dependency in dependencies:
            dep_id = str(dependency or "").strip()
            graph[dep_id].append(step_id)
            indegree[step_id] += 1

    queue = deque([step_id for step_id in step_ids if indegree[step_id] == 0])
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for nxt in graph.get(current, []):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if visited != len(step_ids):
        detail = ExceptionDetail(
            code="PLAN_DEPENDENCY_CYCLE",
            cause="cycle detected in step dependencies",
        )
        raise BaseAppException("계획 단계 의존성에 순환이 있습니다.", detail)


def _to_dependency_list(step: Mapping[str, Any]) -> list[Any]:
    """step의 depends_on 값을 반복 가능한 list[Any]로 정규화한다."""

    raw_dependencies = step.get("depends_on")
    dependencies: list[Any] = []
    if not isinstance(raw_dependencies, list):
        return dependencies
    for dependency in raw_dependencies:
        dependencies.append(dependency)
    return dependencies


def _find_duplicates(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicated: list[str] = []
    for value in values:
        if value in seen and value not in duplicated:
            duplicated.append(value)
        seen.add(value)
    return duplicated

