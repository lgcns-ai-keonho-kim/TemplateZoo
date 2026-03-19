"""
목적: Tool selector/retry JSON 정규화 유틸을 검증한다.
설명: LLM JSON 파싱, ToolCall 생성, retry 대상 검증을 실제 ToolRegistry 기준으로 확인한다.
디자인 패턴: 단위 테스트
참조: src/tool_proxy_agent/core/chat/nodes/_tool_call_selection.py
"""

from __future__ import annotations

import pytest

from tool_proxy_agent.core.chat.nodes._tool_call_selection import (
    build_tool_calls,
    parse_tool_call_json,
)
from tool_proxy_agent.shared.chat.tools.registry import ToolRegistry
from tool_proxy_agent.shared.chat.tools.types import ToolCall, ToolResult
from tool_proxy_agent.shared.exceptions import BaseAppException


def _dummy_tool(tool_call: ToolCall) -> ToolResult:
    """입력 인자를 그대로 돌려주는 테스트용 Tool 함수."""

    return {
        "ok": True,
        "output": {"echo": dict(tool_call.get("args") or {})},
        "error": None,
    }


def _build_registry(*, required_by_default: bool = False) -> ToolRegistry:
    registry = ToolRegistry(validate_module_prefix=False)
    registry.add_tool(
        name="sum_tool",
        description="정수 합산",
        args_schema={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        fn=_dummy_tool,
        required=required_by_default,
    )
    return registry


def test_parse_tool_call_json_reads_object_payload() -> None:
    """selector JSON 객체는 dict로 파싱되어야 한다."""

    parsed = parse_tool_call_json(
        '{"tool_calls":[{"tool_name":"sum_tool","args":{"a":1,"b":2}}]}',
        label="Tool selector",
    )

    assert parsed["tool_calls"][0]["tool_name"] == "sum_tool"


def test_build_tool_calls_creates_tool_call_id_for_selector() -> None:
    """초기 selector 결과는 tool_call_id가 포함된 ToolCall로 정규화되어야 한다."""

    calls = build_tool_calls(
        payload={
            "tool_calls": [
                {
                    "tool_name": "sum_tool",
                    "args": {"a": 1, "b": 2},
                }
            ]
        },
        registry=_build_registry(),
        session_id="session-1",
        request_id="request-1",
        state={"user_message": "합계를 계산해줘"},
        allow_retry_for=False,
    )

    assert len(calls) == 1
    assert calls[0]["tool_call_id"].startswith("tool_call_")
    assert calls[0]["required"] is False
    assert calls[0]["retry_for"] is None


def test_build_tool_calls_allows_optional_tool_to_be_promoted_required() -> None:
    """optional Tool은 step required=true로 필수 승격할 수 있어야 한다."""

    calls = build_tool_calls(
        payload={
            "tool_calls": [
                {
                    "tool_name": "sum_tool",
                    "required": True,
                    "args": {"a": 1, "b": 2},
                }
            ]
        },
        registry=_build_registry(),
        session_id="session-1",
        request_id="request-1",
        state={"user_message": "합계를 계산해줘"},
        allow_retry_for=False,
    )

    assert calls[0]["required"] is True


def test_build_tool_calls_rejects_required_downgrade_for_required_tool() -> None:
    """기본 필수 Tool은 step required=false로 낮출 수 없어야 한다."""

    with pytest.raises(BaseAppException) as error_info:
        build_tool_calls(
            payload={
                "tool_calls": [
                    {
                        "tool_name": "sum_tool",
                        "required": False,
                        "args": {"a": 1, "b": 2},
                    }
                ]
            },
            registry=_build_registry(required_by_default=True),
            session_id="session-1",
            request_id="request-1",
            state={"user_message": "합계를 계산해줘"},
            allow_retry_for=False,
        )

    assert error_info.value.detail.code == "TOOL_REQUIRED_OVERRIDE_INVALID"


def test_build_tool_calls_rejects_unknown_retry_target() -> None:
    """retry selector는 존재하지 않는 실패 식별자를 참조할 수 없다."""

    with pytest.raises(BaseAppException) as error_info:
        build_tool_calls(
            payload={
                "tool_calls": [
                    {
                        "retry_for": "missing-call",
                        "tool_name": "sum_tool",
                        "args": {"a": 1, "b": 2},
                    }
                ]
            },
            registry=_build_registry(),
            session_id="session-1",
            request_id="request-1",
            state={"user_message": "합계를 계산해줘"},
            allow_retry_for=True,
            known_failure_ids={"failed-call-1"},
        )

    assert error_info.value.detail.code == "TOOL_RETRY_SELECTION_INVALID"
