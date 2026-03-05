"""
목적: 응답 생성 입력 준비 노드를 제공한다.
설명: 계획 실행 결과를 응답 LLM 프롬프트 입력(rag_context)으로 변환한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/plan_and_then_execute_agent/core/chat/nodes/response_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plan_and_then_execute_agent.core.chat.nodes._plan_utils import summarize_step_results
from plan_and_then_execute_agent.shared.chat.nodes import function_node
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_response_prepare_logger: Logger = create_default_logger("ResponsePrepareNode")


def _run_response_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    plan_id = str(state.get("plan_id") or "")
    raw_steps = state.get("plan_steps")
    plan_steps = [dict(item) for item in raw_steps if isinstance(item, Mapping)] if isinstance(raw_steps, list) else []

    step_results = state.get("step_results")
    step_failures = state.get("step_failures")

    summary = summarize_step_results(
        plan_id=plan_id,
        plan_steps=plan_steps,
        step_results=dict(step_results) if isinstance(step_results, Mapping) else {},
        step_failures=dict(step_failures) if isinstance(step_failures, Mapping) else {},
    )

    return {
        "rag_context": summary,
        "rag_references": [],
        "plan_execution_summary": summary,
    }


response_prepare_node = function_node(
    fn=_run_response_prepare_step,
    node_name="response_prepare",
    logger=_response_prepare_logger,
)

__all__ = ["response_prepare_node"]
