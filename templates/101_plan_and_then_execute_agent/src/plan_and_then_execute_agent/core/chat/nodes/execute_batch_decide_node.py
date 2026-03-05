"""
목적: batch 실행 후 다음 분기 결정 노드를 제공한다.
설명: 성공/실패 상태와 남은 큐를 기준으로 next_batch/replan/response를 선택한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_execute_batch_decide_logger: Logger = create_default_logger("ExecuteBatchDecideNode")
_MAX_REPLAN_COUNT = 1


def _run_execute_batch_decide_step(state: Mapping[str, Any]) -> dict[str, Any]:
    has_failures = bool(state.get("batch_has_failures") is True)
    replan_count = int(state.get("replan_count") or 0)

    queue = state.get("execute_queue")
    has_remaining_queue = bool(isinstance(queue, list) and len(queue) > 0)

    if has_failures:
        if replan_count < _MAX_REPLAN_COUNT:
            return {"execute_decision": "replan"}

        failure_ids_raw = state.get("batch_failure_ids")
        failure_ids = [str(item).strip() for item in failure_ids_raw if str(item).strip()] if isinstance(failure_ids_raw, list) else []
        detail = ExceptionDetail(
            code="PLAN_EXECUTION_FAILED",
            cause=f"replan_count={replan_count}, failed_steps={','.join(failure_ids)}",
            metadata={
                "replan_count": replan_count,
                "failed_steps": failure_ids,
            },
        )
        raise BaseAppException("계획 실행이 실패했습니다. 재계획 한도를 초과했습니다.", detail)

    if has_remaining_queue:
        return {"execute_decision": "next_batch"}

    return {"execute_decision": "response"}


execute_batch_decide_node = function_node(
    fn=_run_execute_batch_decide_step,
    node_name="execute_batch_decide",
    logger=_execute_batch_decide_logger,
)

__all__ = ["execute_batch_decide_node"]
