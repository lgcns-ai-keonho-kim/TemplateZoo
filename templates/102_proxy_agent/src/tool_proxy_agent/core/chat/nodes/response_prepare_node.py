"""
목적: 응답 생성 입력 준비 노드를 제공한다.
설명: Tool 실행 결과와 optional 실패 경고를 응답 LLM 프롬프트 입력으로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/tool_proxy_agent/core/chat/nodes/response_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tool_proxy_agent.core.chat.nodes._tool_execution_summary import (
    summarize_optional_tool_failures,
    summarize_tool_execution,
)
from tool_proxy_agent.shared.chat.nodes import function_node
from tool_proxy_agent.shared.logging import Logger, create_default_logger

_response_prepare_logger: Logger = create_default_logger("ResponsePrepareNode")


def _run_response_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    completed_tool_results = [
        dict(item)
        for item in state.get("completed_tool_results", [])
        if isinstance(item, Mapping)
    ]
    raw_optional_failures = state.get("unresolved_optional_failures")
    unresolved_optional_failures = [
        dict(item)
        for item in raw_optional_failures
        if isinstance(item, Mapping)
    ] if isinstance(raw_optional_failures, list) else [
        dict(item)
        for item in state.get("unresolved_tool_failures", [])
        if isinstance(item, Mapping) and item.get("required") is not True
    ]
    summary = summarize_tool_execution(
        completed_results=completed_tool_results,
        unresolved_failures=unresolved_optional_failures,
    )
    optional_tool_failure_summary = summarize_optional_tool_failures(
        unresolved_optional_failures
    )

    return {
        "tool_execution_summary": summary,
        "optional_tool_failure_summary": optional_tool_failure_summary,
        "rag_references": [],
    }


response_prepare_node = function_node(
    fn=_run_response_prepare_step,
    node_name="response_prepare",
    logger=_response_prepare_logger,
)

__all__ = ["response_prepare_node"]
