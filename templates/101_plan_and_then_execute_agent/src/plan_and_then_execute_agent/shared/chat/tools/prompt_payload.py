"""
목적: Planner 프롬프트 주입용 Tool payload 빌더를 제공한다.
설명: ToolRegistry/ToolSpec 목록을 LLM 프롬프트에 넣기 쉬운 JSON 문자열로 직렬화한다.
디자인 패턴: 어댑터
참조: src/plan_and_then_execute_agent/shared/chat/tools/registry.py
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from plan_and_then_execute_agent.shared.chat.tools.registry import ToolRegistry
from plan_and_then_execute_agent.shared.chat.tools.types import PlannerToolSpec


def build_planner_tools_payload(
    registry_or_specs: ToolRegistry | Sequence[PlannerToolSpec],
) -> str:
    """Planner 프롬프트에 주입할 Tool 목록 JSON 문자열을 반환한다."""

    if isinstance(registry_or_specs, ToolRegistry):
        specs = registry_or_specs.list_for_planner()
    else:
        specs = list(registry_or_specs)

    payload = {
        "tools": [
            {
                "name": str(item.get("name") or ""),
                "description": str(item.get("description") or ""),
                "args_schema": item.get("args_schema") if isinstance(item.get("args_schema"), dict) else {},
            }
            for item in specs
            if isinstance(item, dict)
        ]
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
