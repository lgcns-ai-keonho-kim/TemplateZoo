"""
목적: Agent LangGraph 상태 타입을 정의한다.
설명: 축소형 tool selector + retry 그래프 실행에 필요한 상태 구조와 병합 리듀서를 제공한다.
디자인 패턴: 상태 객체(State Object)
참조: src/one_shot_tool_calling_agent/core/agent/graphs/agent_graph.py
"""

from __future__ import annotations

from typing_extensions import Annotated, NotRequired, TypedDict

from one_shot_tool_calling_agent.core.agent.models import AgentMessage


def _merge_batch_items(
    left: list[dict[str, object]],
    right: list[dict[str, object]],
) -> list[dict[str, object]]:
    """fan-out Tool 실행 결과 목록을 누적 병합한다."""

    # 빈 리스트는 "현재 배치 결과 초기화" 신호로 사용한다.
    if not right:
        return []
    return [*left, *right]


class AgentGraphState(TypedDict):
    """LangGraph 에이전트 상태 타입."""

    session_id: str
    request_id: NotRequired[str]
    user_message: str
    history: list[AgentMessage]

    safeguard_result: NotRequired[str]
    safeguard_route: NotRequired[str]
    safeguard_reason: NotRequired[str]

    tool_catalog_payload: NotRequired[str]
    tool_selection_raw: NotRequired[str]
    retry_selection_raw: NotRequired[str]
    selection_obj: NotRequired[dict[str, object]]
    retry_selection_obj: NotRequired[dict[str, object]]
    current_tool_calls: NotRequired[list[dict[str, object]]]
    tool_execution_route: NotRequired[str]

    batch_tool_exec_inputs: NotRequired[list[dict[str, object]]]
    batch_tool_results: NotRequired[
        Annotated[list[dict[str, object]], _merge_batch_items]
    ]
    batch_tool_failures: NotRequired[
        Annotated[list[dict[str, object]], _merge_batch_items]
    ]
    completed_tool_results: NotRequired[list[dict[str, object]]]
    unresolved_tool_failures: NotRequired[list[dict[str, object]]]
    retry_count: NotRequired[int]
    retry_decision: NotRequired[str]
    retry_failure_summary: NotRequired[str]
    tool_execution_summary: NotRequired[str]
    rag_references: NotRequired[list[dict[str, object]]]
    assistant_message: str
