"""
목적: Tool retry 진입 여부 결정 노드를 제공한다.
설명: 현재 batch 실패와 retry_count를 기준으로 retry 또는 response를 선택한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/tool_proxy_agent/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tool_proxy_agent.shared.chat.nodes import function_node
from tool_proxy_agent.shared.logging import Logger, create_default_logger

_retry_route_logger: Logger = create_default_logger("RetryRouteNode")
_MAX_RETRY_COUNT = 1


def _run_retry_route_step(state: Mapping[str, Any]) -> dict[str, Any]:
    batch_failures = state.get("batch_tool_failures")
    has_failures = bool(isinstance(batch_failures, list) and batch_failures)
    retry_count = int(state.get("retry_count") or 0)
    if has_failures and retry_count < _MAX_RETRY_COUNT:
        return {"retry_decision": "retry"}
    return {"retry_decision": "response"}


retry_route_node = function_node(
    fn=_run_retry_route_step,
    node_name="retry_route",
    logger=_retry_route_logger,
)

__all__ = ["retry_route_node"]
