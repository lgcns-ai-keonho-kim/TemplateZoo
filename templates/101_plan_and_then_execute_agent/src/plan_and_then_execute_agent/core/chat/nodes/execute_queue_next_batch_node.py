"""
목적: 다음 실행 batch 선택 노드를 제공한다.
설명: execute_queue에서 다음 batch를 꺼내 current_batch와 실행 분기를 설정한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/execute_batch_prepare_node.py
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_execute_queue_next_batch_logger: Logger = create_default_logger("ExecuteQueueNextBatchNode")


def _run_execute_queue_next_batch_step(state: Mapping[str, Any]) -> dict[str, Any]:
    raw_queue = state.get("execute_queue")
    queue: list[list[str]] = []
    if isinstance(raw_queue, list):
        for item in raw_queue:
            if not isinstance(item, list):
                continue
            batch = [str(step_id).strip() for step_id in item if str(step_id).strip()]
            if batch:
                queue.append(batch)

    if not queue:
        return {
            "current_batch": [],
            "execute_queue": [],
            "batch_expected_count": 0,
            "current_batch_started_at": 0.0,
            "execute_decision": "response",
        }

    current_batch = queue[0]
    remaining = queue[1:]
    return {
        "current_batch": current_batch,
        "execute_queue": remaining,
        "batch_expected_count": len(current_batch),
        "current_batch_started_at": time.monotonic(),
        "batch_tool_exec_inputs": [],
        "batch_tool_results": [],
        "batch_tool_failures": [],
        "execute_decision": "execute",
    }


execute_queue_next_batch_node = function_node(
    fn=_run_execute_queue_next_batch_step,
    node_name="execute_queue_next_batch",
    logger=_execute_queue_next_batch_logger,
)

__all__ = ["execute_queue_next_batch_node"]
