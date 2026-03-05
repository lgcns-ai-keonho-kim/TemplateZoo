"""
목적: ToolRegistry 최소 인터페이스 동작을 검증한다.
설명: get_tools/list_specs/list_for_planner 반환 형태와 하위 호환 동작을 확인한다.
디자인 패턴: 단위 테스트
참조: src/plan_and_then_execute_agent/shared/chat/tools/registry.py
"""

from __future__ import annotations

from plan_and_then_execute_agent.shared.chat.tools.registry import ToolRegistry
from plan_and_then_execute_agent.shared.chat.tools.types import ToolCall, ToolResult


def _dummy_tool(tool_call: ToolCall) -> ToolResult:
    """입력값을 그대로 반환하는 테스트용 Tool 함수."""

    return {
        "ok": True,
        "output": {"echo": dict(tool_call.get("args") or {})},
        "error": None,
    }


def test_get_tools_returns_tuple_snapshot_in_registration_order() -> None:
    """get_tools는 등록 순서를 유지한 읽기 전용 튜플을 반환해야 한다."""

    registry = ToolRegistry(validate_module_prefix=False)
    registry.add_tool(
        name="alpha",
        description="alpha tool",
        args_schema={"type": "object", "properties": {}, "additionalProperties": False},
        fn=_dummy_tool,
    )
    registry.add_tool(
        name="beta",
        description="beta tool",
        args_schema={"type": "object", "properties": {}, "additionalProperties": False},
        fn=_dummy_tool,
    )

    tools = registry.get_tools()
    assert isinstance(tools, tuple)
    assert [spec.name for spec in tools] == ["alpha", "beta"]


def test_list_specs_keeps_backward_compatible_result() -> None:
    """list_specs는 기존과 동일하게 list를 반환해야 한다."""

    registry = ToolRegistry(validate_module_prefix=False)
    registry.add_tool(
        name="only_one",
        description="single tool",
        args_schema={"type": "object", "properties": {}, "additionalProperties": False},
        fn=_dummy_tool,
    )

    specs = registry.list_specs()
    assert isinstance(specs, list)
    assert len(specs) == 1
    assert specs[0].name == "only_one"


def test_list_for_planner_uses_registered_specs() -> None:
    """Planner 노출 스펙은 등록된 Tool 정보와 동일해야 한다."""

    registry = ToolRegistry(validate_module_prefix=False)
    registry.add_tool(
        name="sum_tool",
        description="two numbers sum",
        args_schema={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        fn=_dummy_tool,
    )

    planner_specs = registry.list_for_planner()
    assert len(planner_specs) == 1
    assert planner_specs[0]["name"] == "sum_tool"
    assert planner_specs[0]["description"] == "two numbers sum"
    assert planner_specs[0]["args_schema"]["required"] == ["a", "b"]
