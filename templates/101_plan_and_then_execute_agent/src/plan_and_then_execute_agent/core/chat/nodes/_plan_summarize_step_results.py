"""
목적: 실행 결과 요약 유틸을 제공한다.
설명: response 노드 입력용으로 단계별 성공/실패/출력 요약을 생성한다.
디자인 패턴: 유틸리티
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any


def summarize_step_results(
    *,
    plan_id: str,
    plan_steps: Sequence[Mapping[str, Any]],
    step_results: Mapping[str, Any] | None,
    step_failures: Mapping[str, Any] | None,
) -> str:
    """response 노드 입력용 실행 결과 컨텍스트를 생성한다."""

    lines: list[str] = ["[Plan Execution Summary]", f"- plan_id: {plan_id}"]

    result_map = dict(step_results or {})
    failure_map = dict(step_failures or {})
    if not plan_steps:
        lines.append("- no steps")
        return "\n".join(lines)

    for step in plan_steps:
        step_id = str(step.get("id") or "")
        goal = str(step.get("goal") or "")
        tool_name = str(step.get("tool_name") or "")
        lines.append(f"\n[Step] id={step_id}, tool={tool_name}, goal={goal}")

        failure = failure_map.get(step_id)
        if isinstance(failure, Mapping):
            error_message = str(failure.get("error") or "failed")
            lines.append(f"- status: FAILED")
            lines.append(f"- error: {error_message}")
            continue

        result = result_map.get(step_id)
        if isinstance(result, Mapping):
            output = result.get("output")
            lines.append("- status: SUCCESS")
            if isinstance(output, Mapping):
                try:
                    lines.append(f"- output: {json.dumps(dict(output), ensure_ascii=False)}")
                except TypeError:
                    lines.append(f"- output: {str(output)}")
            else:
                lines.append(f"- output: {str(output)}")
            continue

        lines.append("- status: SKIPPED")

    return "\n".join(lines)

