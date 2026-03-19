"""
목적: Tool retry 진입 여부 결정 노드를 제공한다.
설명: 현재 batch 실패와 retry_count, required 미해결 실패를 기준으로 retry/response/error를 선택한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/tool_proxy_agent/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tool_proxy_agent.shared.exceptions import BaseAppException, ExceptionDetail
from tool_proxy_agent.shared.chat.nodes import function_node
from tool_proxy_agent.shared.logging import Logger, create_default_logger

_retry_route_logger: Logger = create_default_logger("RetryRouteNode")
_MAX_RETRY_COUNT = 1


def _as_mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _summarize_failure_targets(failures: list[dict[str, Any]]) -> tuple[str, str]:
    tool_names = sorted(
        {
            str(item.get("tool_name") or "").strip()
            for item in failures
            if str(item.get("tool_name") or "").strip()
        }
    )
    tool_call_ids = [
        str(item.get("tool_call_id") or "").strip()
        for item in failures
        if str(item.get("tool_call_id") or "").strip()
    ]
    return ",".join(tool_names), ",".join(tool_call_ids)


def _run_retry_route_step(state: Mapping[str, Any]) -> dict[str, Any]:
    batch_failures = state.get("batch_tool_failures")
    has_failures = bool(isinstance(batch_failures, list) and batch_failures)
    retry_count = int(state.get("retry_count") or 0)
    if has_failures and retry_count < _MAX_RETRY_COUNT:
        return {"retry_decision": "retry"}
    unresolved_required_failures = _as_mapping_list(
        state.get("unresolved_required_failures")
    )
    if not unresolved_required_failures:
        unresolved_required_failures = [
            item
            for item in _as_mapping_list(state.get("unresolved_tool_failures"))
            if item.get("required") is True
        ]
    if not unresolved_required_failures:
        unresolved_required_failures = [
            item for item in _as_mapping_list(batch_failures) if item.get("required") is True
        ]
    if unresolved_required_failures:
        failed_tools, failed_call_ids = _summarize_failure_targets(
            unresolved_required_failures
        )
        detail = ExceptionDetail(
            code="TOOL_REQUIRED_FAILURE",
            cause=(
                f"retry_count={retry_count}, "
                f"tool_names={failed_tools}, tool_call_ids={failed_call_ids}"
            ),
            metadata={
                "retry_count": retry_count,
                "tool_names": failed_tools,
                "tool_call_ids": failed_call_ids,
            },
        )
        raise BaseAppException(
            "필수 Tool 실행이 끝내 복구되지 않아 요청을 완료할 수 없습니다.",
            detail,
        )
    return {"retry_decision": "response"}


retry_route_node = function_node(
    fn=_run_retry_route_step,
    node_name="retry_route",
    logger=_retry_route_logger,
)

__all__ = ["retry_route_node"]
