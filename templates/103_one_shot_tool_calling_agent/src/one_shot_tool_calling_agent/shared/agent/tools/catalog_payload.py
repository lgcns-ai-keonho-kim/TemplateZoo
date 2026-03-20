"""
목적: Tool selector 입력용 Tool 카탈로그 payload 빌더를 제공한다.
설명: ToolRegistry 또는 ToolSpec 목록을 LLM 프롬프트에 넣기 쉬운 JSON 문자열로 직렬화한다.
디자인 패턴: 어댑터
참조: src/one_shot_tool_calling_agent/shared/agent/tools/registry.py
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from one_shot_tool_calling_agent.shared.agent.tools.registry import ToolRegistry
from one_shot_tool_calling_agent.shared.agent.tools.types import SelectorToolSpec


def build_tool_catalog_payload(
    registry_or_specs: ToolRegistry | Sequence[SelectorToolSpec],
) -> str:
    """Tool selector에 주입할 Tool 목록 JSON 문자열을 반환한다."""

    if isinstance(registry_or_specs, ToolRegistry):
        specs = registry_or_specs.list_for_selector()
    else:
        specs = list(registry_or_specs)

    payload = {
        "tools": [
            {
                "name": str(item.get("name") or ""),
                "description": str(item.get("description") or ""),
                "args_schema": (
                    item.get("args_schema")
                    if isinstance(item.get("args_schema"), dict)
                    else {}
                ),
            }
            for item in specs
            if isinstance(item, dict)
        ]
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


__all__ = ["build_tool_catalog_payload"]
