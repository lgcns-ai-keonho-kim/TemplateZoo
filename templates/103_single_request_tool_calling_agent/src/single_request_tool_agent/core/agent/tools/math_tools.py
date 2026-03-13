"""
목적: 숫자 연산 예시 Tool을 제공한다.
설명: ToolCall에서 인자를 읽어 두 정수를 더한 결과를 반환한다.
디자인 패턴: 단일 책임 함수
참조: src/single_request_tool_agent/shared/agent/tools/types.py
"""

from __future__ import annotations

from typing import Any

from single_request_tool_agent.shared.agent.tools.types import ToolCall, ToolResult


def add_number(tool_call: ToolCall) -> ToolResult:
    """ToolCall 인자 `a`, `b`를 정수 덧셈해 반환한다."""

    args: dict[str, Any] = dict(tool_call.get("args") or {})
    raw_a = args.get("a")
    raw_b = args.get("b")
    if raw_a is None or raw_b is None:
        return {
            "ok": False,
            "output": {},
            "error": "a 또는 b 인자가 누락되었습니다.",
        }
    a = int(raw_a)
    b = int(raw_b)
    value = int(a) + int(b)
    return {
        "ok": True,
        "output": {"value": value},
        "error": None,
    }
