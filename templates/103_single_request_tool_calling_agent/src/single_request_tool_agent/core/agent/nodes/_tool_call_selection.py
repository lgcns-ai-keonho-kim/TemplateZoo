"""
목적: Tool selector/retry JSON 파싱과 호출 정규화를 제공한다.
설명: LLM이 반환한 tool_calls JSON을 복구 파싱하고 ToolRegistry 기준으로 실행 가능한 ToolCall 목록으로 검증한다.
디자인 패턴: 유틸리티
참조: src/single_request_tool_agent/shared/agent/tools/schema_validator.py
"""

from __future__ import annotations

import json
from collections.abc import Collection, Mapping
from typing import Any
from uuid import uuid4

from json_repair import repair_json

from single_request_tool_agent.shared.agent.tools import (
    ToolCall,
    ToolRegistry,
    validate_tool_args_schema,
)
from single_request_tool_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)


def parse_tool_call_json(raw: str, *, label: str) -> dict[str, Any]:
    """LLM 출력 문자열을 tool_calls JSON 객체로 파싱한다."""

    text = str(raw or "").strip()
    if not text:
        detail = ExceptionDetail(
            code="TOOL_SELECTION_EMPTY",
            cause=f"{label} raw output is empty",
        )
        raise BaseAppException(f"{label} JSON 출력이 비어 있습니다.", detail)

    candidate = _extract_json_candidate(text)
    parsed = _try_load_json_object(candidate)
    if parsed is not None:
        return parsed

    repaired = repair_json(candidate, return_objects=True)
    if isinstance(repaired, tuple):
        repaired = repaired[0]
    if isinstance(repaired, dict):
        return {str(key): value for key, value in repaired.items()}

    detail = ExceptionDetail(
        code="TOOL_SELECTION_INVALID",
        cause=f"{label} output is not a valid JSON object",
    )
    raise BaseAppException(f"{label} JSON 파싱에 실패했습니다.", detail)


def build_tool_calls(
    *,
    payload: Mapping[str, Any],
    registry: ToolRegistry,
    session_id: str,
    request_id: str,
    state: Mapping[str, Any],
    allow_retry_for: bool,
    known_failure_ids: Collection[str] = (),
) -> list[ToolCall]:
    """selector/retry JSON payload를 실행 가능한 ToolCall 목록으로 검증한다."""

    raw_tool_calls = payload.get("tool_calls")
    if raw_tool_calls is None:
        return []
    if not isinstance(raw_tool_calls, list):
        detail = ExceptionDetail(
            code="TOOL_SELECTION_INVALID",
            cause=f"tool_calls_type={type(raw_tool_calls).__name__}",
        )
        raise BaseAppException("tool_calls 필드는 배열이어야 합니다.", detail)

    known_failure_id_set = {
        str(item).strip() for item in known_failure_ids if str(item).strip()
    }
    seen_retry_targets: set[str] = set()
    validated_calls: list[ToolCall] = []

    for raw_item in raw_tool_calls:
        if not isinstance(raw_item, Mapping):
            detail = ExceptionDetail(
                code="TOOL_SELECTION_INVALID",
                cause=f"tool_call_type={type(raw_item).__name__}",
            )
            raise BaseAppException("각 tool_calls 항목은 객체여야 합니다.", detail)

        tool_name = str(raw_item.get("tool_name") or "").strip()
        if not tool_name:
            detail = ExceptionDetail(
                code="TOOL_SELECTION_INVALID",
                cause="tool_name is empty",
            )
            raise BaseAppException("Tool 이름이 누락되었습니다.", detail)

        spec = registry.resolve(tool_name)
        raw_args = raw_item.get("args")
        validated_args = validate_tool_args_schema(
            tool_name=tool_name,
            args_schema=spec.args_schema,
            raw_args=raw_args if raw_args is not None else {},
        )

        retry_for = _normalize_retry_for(raw_item.get("retry_for"))
        if allow_retry_for:
            if retry_for is None:
                detail = ExceptionDetail(
                    code="TOOL_RETRY_SELECTION_INVALID",
                    cause=f"tool_name={tool_name}, retry_for is missing",
                )
                raise BaseAppException("재시도 대상 식별자가 누락되었습니다.", detail)
            if retry_for not in known_failure_id_set:
                detail = ExceptionDetail(
                    code="TOOL_RETRY_SELECTION_INVALID",
                    cause=f"tool_name={tool_name}, retry_for={retry_for}",
                )
                raise BaseAppException(
                    "재시도 대상 식별자가 유효하지 않습니다.", detail
                )
            if retry_for in seen_retry_targets:
                detail = ExceptionDetail(
                    code="TOOL_RETRY_SELECTION_DUPLICATE",
                    cause=f"retry_for={retry_for}",
                )
                raise BaseAppException(
                    "동일한 실패 항목을 중복 재시도할 수 없습니다.", detail
                )
            seen_retry_targets.add(retry_for)
        else:
            retry_for = None

        validated_calls.append(
            {
                "tool_call_id": _build_tool_call_id(),
                "tool_name": tool_name,
                "args": validated_args,
                "session_id": session_id,
                "request_id": request_id,
                "retry_for": retry_for,
                "state": state,
            }
        )

    return validated_calls


def _build_tool_call_id() -> str:
    return f"tool_call_{uuid4().hex}"


def _normalize_retry_for(raw_retry_for: object) -> str | None:
    candidate = str(raw_retry_for or "").strip()
    if not candidate:
        return None
    return candidate


def _extract_json_candidate(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _try_load_json_object(text: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(loaded, dict):
        return None
    return {str(key): value for key, value in loaded.items()}


__all__ = ["parse_tool_call_json", "build_tool_calls"]
