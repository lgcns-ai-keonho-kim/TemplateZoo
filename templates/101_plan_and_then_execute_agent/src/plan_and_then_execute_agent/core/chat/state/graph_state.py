"""
목적: Chat LangGraph 상태 타입을 정의한다.
설명: Plan-and-then-Execute 그래프 실행에 필요한 상태 구조와 병합 리듀서를 제공한다.
디자인 패턴: 상태 객체(State Object)
참조: src/plan_and_then_execute_agent/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from typing_extensions import Annotated, NotRequired, TypedDict

from plan_and_then_execute_agent.core.chat.models import ChatMessage


def _merge_batch_items(
    left: list[dict[str, object]],
    right: list[dict[str, object]],
) -> list[dict[str, object]]:
    """fan-out Tool 실행 결과 목록을 누적 병합한다."""

    # 빈 리스트는 "현재 배치 결과 초기화" 신호로 사용한다.
    if not right:
        return []
    return [*left, *right]


class ChatGraphState(TypedDict):
    """LangGraph 대화 상태 타입."""

    session_id: str
    request_id: NotRequired[str]
    user_message: str
    history: list[ChatMessage]

    safeguard_result: NotRequired[str]
    safeguard_route: NotRequired[str]
    safeguard_reason: NotRequired[str]

    planner_history_summary: NotRequired[str]
    planner_tools_payload: NotRequired[str]
    available_tool_names: NotRequired[list[str]]

    plan_raw: NotRequired[str]
    replan_raw: NotRequired[str]
    plan_obj: NotRequired[dict[str, object]]
    plan_id: NotRequired[str]
    plan_steps: NotRequired[list[dict[str, object]]]

    execute_queue: NotRequired[list[list[str]]]
    execute_decision: NotRequired[str]

    current_batch: NotRequired[list[str]]
    current_batch_started_at: NotRequired[float]
    batch_expected_count: NotRequired[int]
    batch_tool_exec_inputs: NotRequired[list[dict[str, object]]]
    batch_tool_results: NotRequired[
        Annotated[list[dict[str, object]], _merge_batch_items]
    ]
    batch_tool_failures: NotRequired[
        Annotated[list[dict[str, object]], _merge_batch_items]
    ]
    batch_failure_ids: NotRequired[list[str]]
    batch_has_failures: NotRequired[bool]
    batch_elapsed_seconds: NotRequired[float]
    batch_timeout_exceeded: NotRequired[bool]

    step_results: NotRequired[dict[str, dict[str, object]]]
    step_failures: NotRequired[dict[str, dict[str, object]]]

    step_timeout_seconds: NotRequired[float]
    replan_count: NotRequired[int]
    replan_previous_plan_summary: NotRequired[str]
    replan_failure_summary: NotRequired[str]

    plan_execution_summary: NotRequired[str]
    rag_context: NotRequired[str]
    rag_references: NotRequired[list[dict[str, object]]]
    assistant_message: str
