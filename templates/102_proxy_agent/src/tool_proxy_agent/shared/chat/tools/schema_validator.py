"""
목적: Tool args_schema 최소 검증기를 제공한다.
설명: 현재 ToolRegistry에서 사용하는 JSON Schema 부분집합만 검증해 selector/retry 결과를 안전하게 정규화한다.
디자인 패턴: 유틸리티
참조: src/tool_proxy_agent/shared/chat/tools/registry.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tool_proxy_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)


def validate_tool_args_schema(
    *,
    tool_name: str,
    args_schema: Mapping[str, Any],
    raw_args: object,
) -> dict[str, Any]:
    """Tool args를 현재 지원하는 schema 규칙으로 검증한다."""

    if not isinstance(raw_args, Mapping):
        detail = ExceptionDetail(
            code="TOOL_ARGS_INVALID",
            cause=f"tool_name={tool_name}, args_type={type(raw_args).__name__}",
        )
        raise BaseAppException("Tool 인자 형식이 올바르지 않습니다.", detail)

    schema_type = str(args_schema.get("type") or "object").strip().lower()
    if schema_type != "object":
        detail = ExceptionDetail(
            code="TOOL_ARGS_SCHEMA_UNSUPPORTED",
            cause=f"tool_name={tool_name}, schema_type={schema_type}",
        )
        raise BaseAppException("지원하지 않는 Tool 스키마입니다.", detail)

    properties = args_schema.get("properties")
    property_map = dict(properties) if isinstance(properties, Mapping) else {}
    required = _normalize_required(args_schema.get("required"))
    allow_additional = bool(args_schema.get("additionalProperties", True))

    normalized_args = {str(key): value for key, value in raw_args.items()}

    for required_key in required:
        if required_key not in normalized_args:
            detail = ExceptionDetail(
                code="TOOL_ARGS_REQUIRED_MISSING",
                cause=f"tool_name={tool_name}, field={required_key}",
            )
            raise BaseAppException("필수 Tool 인자가 누락되었습니다.", detail)

    if not allow_additional:
        unexpected_keys = sorted(set(normalized_args) - set(property_map))
        if unexpected_keys:
            detail = ExceptionDetail(
                code="TOOL_ARGS_UNEXPECTED_FIELD",
                cause=(
                    f"tool_name={tool_name}, unexpected={','.join(unexpected_keys)}"
                ),
            )
            raise BaseAppException(
                "허용되지 않은 Tool 인자가 포함되어 있습니다.", detail
            )

    for field_name, value in normalized_args.items():
        property_schema = property_map.get(field_name)
        if not isinstance(property_schema, Mapping):
            if allow_additional:
                continue
            detail = ExceptionDetail(
                code="TOOL_ARGS_UNEXPECTED_FIELD",
                cause=f"tool_name={tool_name}, field={field_name}",
            )
            raise BaseAppException(
                "허용되지 않은 Tool 인자가 포함되어 있습니다.", detail
            )
        _validate_scalar_type(
            tool_name=tool_name,
            field_name=field_name,
            schema=property_schema,
            value=value,
        )

    return normalized_args


def _normalize_required(raw_required: object) -> set[str]:
    if not isinstance(raw_required, list):
        return set()
    return {str(item).strip() for item in raw_required if str(item).strip()}


def _validate_scalar_type(
    *,
    tool_name: str,
    field_name: str,
    schema: Mapping[str, Any],
    value: object,
) -> None:
    schema_type = str(schema.get("type") or "").strip().lower()
    if not schema_type:
        return

    is_valid = False
    if schema_type == "string":
        is_valid = isinstance(value, str)
    elif schema_type == "integer":
        is_valid = isinstance(value, int) and not isinstance(value, bool)
    elif schema_type == "number":
        is_valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif schema_type == "boolean":
        is_valid = isinstance(value, bool)
    elif schema_type == "object":
        is_valid = isinstance(value, Mapping)
    elif schema_type == "array":
        is_valid = isinstance(value, list)
    else:
        detail = ExceptionDetail(
            code="TOOL_ARGS_SCHEMA_UNSUPPORTED",
            cause=(
                f"tool_name={tool_name}, field={field_name}, schema_type={schema_type}"
            ),
        )
        raise BaseAppException("지원하지 않는 Tool 스키마입니다.", detail)

    if is_valid:
        return

    detail = ExceptionDetail(
        code="TOOL_ARGS_TYPE_MISMATCH",
        cause=(
            f"tool_name={tool_name}, field={field_name}, "
            f"expected={schema_type}, actual={type(value).__name__}"
        ),
    )
    raise BaseAppException("Tool 인자 타입이 스키마와 다릅니다.", detail)


__all__ = ["validate_tool_args_schema"]
