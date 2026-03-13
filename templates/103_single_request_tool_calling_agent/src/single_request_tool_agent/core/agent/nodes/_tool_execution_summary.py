"""
목적: Tool 실행 결과 요약 유틸을 제공한다.
설명: 성공/실패 Tool 실행 내역을 retry 프롬프트와 최종 응답 프롬프트에 넣기 쉬운 문자열로 정리한다.
디자인 패턴: 유틸리티
참조: src/single_request_tool_agent/core/agent/nodes/response_prepare_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def summarize_tool_execution(
    *,
    completed_results: list[dict[str, Any]],
    unresolved_failures: list[dict[str, Any]],
) -> str:
    """성공/실패 Tool 실행 내역을 단일 문자열로 요약한다."""

    if not completed_results and not unresolved_failures:
        return "도구 실행 없음"

    lines: list[str] = []
    if completed_results:
        lines.append("[성공한 도구 실행]")
        for item in completed_results:
            tool_call_id = str(item.get("tool_call_id") or "")
            tool_name = str(item.get("tool_name") or "")
            output = _compact_output(item.get("output"))
            lines.append(
                f"- tool_call_id={tool_call_id}, tool_name={tool_name}, output={output}"
            )

    if unresolved_failures:
        if lines:
            lines.append("")
        lines.append("[실패한 도구 실행]")
        for item in unresolved_failures:
            tool_call_id = str(item.get("tool_call_id") or "")
            tool_name = str(item.get("tool_name") or "")
            error_code = str(item.get("error_code") or "")
            error_message = str(item.get("error") or "")
            retry_for = str(item.get("retry_for") or "")
            suffix = f", retry_for={retry_for}" if retry_for else ""
            lines.append(
                "- "
                f"tool_call_id={tool_call_id}, tool_name={tool_name}, "
                f"error_code={error_code}, error={error_message}{suffix}"
            )

    return "\n".join(lines)


def summarize_retry_targets(failures: list[dict[str, Any]]) -> str:
    """retry 대상 실패 항목만 간단히 요약한다."""

    if not failures:
        return "재시도 대상 없음"

    lines = ["[재시도 대상]"]
    for item in failures:
        tool_call_id = str(item.get("tool_call_id") or "")
        tool_name = str(item.get("tool_name") or "")
        args = _compact_output(item.get("args"))
        error_code = str(item.get("error_code") or "")
        error_message = str(item.get("error") or "")
        lines.append(
            "- "
            f"tool_call_id={tool_call_id}, tool_name={tool_name}, args={args}, "
            f"error_code={error_code}, error={error_message}"
        )
    return "\n".join(lines)


def _compact_output(raw_output: object) -> str:
    if isinstance(raw_output, Mapping):
        normalized = {str(key): value for key, value in raw_output.items()}
        if "value" in normalized:
            return str(normalized.get("value"))
        preview = ", ".join(
            f"{key}={value!r}" for key, value in list(normalized.items())[:3]
        )
        return preview or "{}"
    if isinstance(raw_output, list):
        return str(raw_output[:3])
    return str(raw_output)


__all__ = ["summarize_tool_execution", "summarize_retry_targets"]
