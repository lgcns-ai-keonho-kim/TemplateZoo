"""
목적: 기존 planner 호환용 Tool payload 빌더를 제공한다.
설명: 내부 구현은 selector용 Tool catalog payload 빌더를 재사용한다.
디자인 패턴: 어댑터
참조: src/tool_proxy_agent/shared/chat/tools/registry.py
"""

from __future__ import annotations

from collections.abc import Sequence

from tool_proxy_agent.shared.chat.tools.catalog_payload import (
    build_tool_catalog_payload,
)
from tool_proxy_agent.shared.chat.tools.registry import ToolRegistry
from tool_proxy_agent.shared.chat.tools.types import PlannerToolSpec


def build_planner_tools_payload(
    registry_or_specs: ToolRegistry | Sequence[PlannerToolSpec],
) -> str:
    """기존 planner 호환용 Tool 목록 JSON 문자열을 반환한다."""

    return build_tool_catalog_payload(registry_or_specs)
