"""
목적: 응답 생성 입력 준비 노드를 제공한다.
설명: Tool 실행 결과를 응답 LLM 프롬프트 입력(tool_execution_summary)으로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/one_shot_tool_calling_agent/core/agent/nodes/response_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from one_shot_tool_calling_agent.core.agent.nodes._tool_execution_summary import (
    summarize_tool_execution,
)
from one_shot_tool_calling_agent.shared.agent.nodes import function_node
from one_shot_tool_calling_agent.shared.logging import Logger, create_default_logger

_response_prepare_logger: Logger = create_default_logger("ResponsePrepareNode")


def _run_response_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    completed_tool_results = [
        dict(item)
        for item in state.get("completed_tool_results", [])
        if isinstance(item, Mapping)
    ]
    unresolved_tool_failures = [
        dict(item)
        for item in state.get("unresolved_tool_failures", [])
        if isinstance(item, Mapping)
    ]
    summary = summarize_tool_execution(
        completed_results=completed_tool_results,
        unresolved_failures=unresolved_tool_failures,
    )

    return {
        "tool_execution_summary": summary,
        "rag_references": [],
    }


response_prepare_node = function_node(
    fn=_run_response_prepare_step,
    node_name="response_prepare",
    logger=_response_prepare_logger,
)

__all__ = ["response_prepare_node"]
