"""
목적: Tool args_schema 최소 검증기를 검증한다.
설명: selector/retry 검증에 필요한 필수 필드, 추가 필드, 타입 오류를 실제 schema로 확인한다.
디자인 패턴: 단위 테스트
참조: src/one_shot_tool_calling_agent/shared/agent/tools/schema_validator.py
"""

from __future__ import annotations

import pytest

from one_shot_tool_calling_agent.shared.agent.tools.schema_validator import (
    validate_tool_args_schema,
)
from one_shot_tool_calling_agent.shared.exceptions import BaseAppException


def test_validate_tool_args_schema_accepts_supported_object_schema() -> None:
    """지원하는 object schema는 정상 통과해야 한다."""

    validated = validate_tool_args_schema(
        tool_name="sum_tool",
        args_schema={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        raw_args={"a": 1, "b": 2},
    )

    assert validated == {"a": 1, "b": 2}


def test_validate_tool_args_schema_rejects_missing_required_field() -> None:
    """필수 필드가 없으면 예외를 발생시켜야 한다."""

    with pytest.raises(BaseAppException) as error_info:
        validate_tool_args_schema(
            tool_name="sum_tool",
            args_schema={
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
                "additionalProperties": False,
            },
            raw_args={"a": 1},
        )

    assert error_info.value.detail.code == "TOOL_ARGS_REQUIRED_MISSING"


def test_validate_tool_args_schema_rejects_unexpected_field() -> None:
    """추가 필드 금지 schema에서는 정의되지 않은 필드를 거부해야 한다."""

    with pytest.raises(BaseAppException) as error_info:
        validate_tool_args_schema(
            tool_name="sum_tool",
            args_schema={
                "type": "object",
                "properties": {"a": {"type": "integer"}},
                "required": ["a"],
                "additionalProperties": False,
            },
            raw_args={"a": 1, "extra": "x"},
        )

    assert error_info.value.detail.code == "TOOL_ARGS_UNEXPECTED_FIELD"
