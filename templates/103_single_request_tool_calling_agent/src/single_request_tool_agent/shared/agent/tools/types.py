"""
목적: Tool Registry/Executor 공통 타입을 정의한다.
설명: ToolCall/ToolResult/ToolSpec 모델과 selector 실행 함수 타입을 제공한다.
디자인 패턴: 타입 객체
참조: src/single_request_tool_agent/shared/agent/tools/registry.py, src/single_request_tool_agent/shared/agent/nodes/tool_exec_node.py
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias, TypedDict


class ToolCall(TypedDict):
    """Tool 실행 요청 컨텍스트."""

    tool_call_id: str
    tool_name: str
    args: dict[str, Any]
    session_id: str
    request_id: str
    retry_for: str | None
    state: Mapping[str, Any]


class ToolResult(TypedDict):
    """Tool 실행 결과 표준 포맷."""

    ok: bool
    output: dict[str, Any]
    error: str | None


class SelectorToolSpec(TypedDict):
    """Tool selector 프롬프트 주입용 Tool 스펙."""

    name: str
    description: str
    args_schema: dict[str, Any]


PlannerToolSpec = SelectorToolSpec


ToolFn: TypeAlias = Callable[[ToolCall], ToolResult | Awaitable[ToolResult]]


@dataclass(frozen=True)
class ToolSpec:
    """Tool Registry 내부 저장 스펙."""

    name: str
    description: str
    args_schema: dict[str, Any]
    fn: ToolFn
    timeout_seconds: float = 30.0
    retry_count: int = 2
    retry_backoff_seconds: tuple[float, ...] = (0.5, 1.0)
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.name or "").strip():
            raise ValueError("tool name은 비어 있을 수 없습니다.")
        if not callable(self.fn):
            raise ValueError("tool fn은 callable 이어야 합니다.")
        if not isinstance(self.args_schema, dict):
            raise ValueError("args_schema는 dict 이어야 합니다.")
        if float(self.timeout_seconds) <= 0:
            raise ValueError("timeout_seconds는 0보다 커야 합니다.")
        if int(self.retry_count) < 0:
            raise ValueError("retry_count는 0 이상이어야 합니다.")
        for delay in self.retry_backoff_seconds:
            if float(delay) < 0:
                raise ValueError("retry_backoff_seconds는 음수가 될 수 없습니다.")

    def to_selector_spec(self) -> SelectorToolSpec:
        """Tool selector에 주입할 최소 스펙을 반환한다."""

        return {
            "name": str(self.name),
            "description": str(self.description),
            "args_schema": dict(self.args_schema),
        }

    def to_planner_spec(self) -> PlannerToolSpec:
        """기존 planner 호환용 최소 스펙을 반환한다."""

        return self.to_selector_spec()
