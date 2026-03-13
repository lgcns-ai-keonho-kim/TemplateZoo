"""
목적: Tool retry 입력 준비 노드를 제공한다.
설명: 최근 batch 실패 요약과 성공/실패 실행 요약을 생성하고 retry 횟수를 증가시킨다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/single_request_tool_agent/core/agent/nodes/_tool_execution_summary.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from single_request_tool_agent.core.agent.nodes._tool_execution_summary import (
    summarize_retry_targets,
    summarize_tool_execution,
)
from single_request_tool_agent.core.agent.tools.registry import registry
from single_request_tool_agent.shared.agent.nodes import function_node
from single_request_tool_agent.shared.agent.tools import build_tool_catalog_payload
from single_request_tool_agent.shared.logging import Logger, create_default_logger

_retry_prepare_logger: Logger = create_default_logger("RetryPrepareNode")


def _as_mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _run_retry_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    completed_results = _as_mapping_list(state.get("completed_tool_results"))
    batch_failures = _as_mapping_list(state.get("batch_tool_failures"))
    return {
        "tool_catalog_payload": build_tool_catalog_payload(registry),
        "tool_execution_summary": summarize_tool_execution(
            completed_results=completed_results,
            unresolved_failures=batch_failures,
        ),
        "retry_failure_summary": summarize_retry_targets(batch_failures),
        "retry_count": int(state.get("retry_count") or 0) + 1,
    }


retry_prepare_node = function_node(
    fn=_run_retry_prepare_step,
    node_name="retry_prepare",
    logger=_retry_prepare_logger,
)

__all__ = ["retry_prepare_node"]
