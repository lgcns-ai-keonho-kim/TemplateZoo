"""
목적: Chat LangGraph 상태 타입을 정의한다.
설명: raw SQL 기반 파이프라인에서 입력/출력으로 전달되는 상태 구조를 정의한다.
디자인 패턴: 상태 객체
참조: src/text_to_sql/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from text_to_sql.core.chat.models import ChatMessage


class ChatGraphState(TypedDict):
    """LangGraph 대화 상태 타입."""

    session_id: str
    user_message: str
    history: list[ChatMessage]

    safeguard_result: NotRequired[str]
    safeguard_route: NotRequired[str]
    safeguard_reason: NotRequired[str]

    context_strategy: NotRequired[str]
    context_strategy_raw: NotRequired[str]
    last_assistant_message: NotRequired[str]
    last_answer_source_meta: NotRequired[dict[str, object]]
    answer_source_meta: NotRequired[dict[str, object]]
    metadata_summary: NotRequired[str]
    metadata_route: NotRequired[str]

    schema_snapshot: NotRequired[dict[str, dict[str, object]]]

    available_target_aliases: NotRequired[list[str]]
    schema_selection_context: NotRequired[str]
    schema_selection_raw: NotRequired[str]
    selected_target_aliases: NotRequired[list[str]]

    raw_sql_inputs: NotRequired[list[dict[str, object]]]
    sql_texts_by_alias: NotRequired[dict[str, str]]
    sql_retry_feedbacks: NotRequired[dict[str, str]]
    retry_count_by_alias: NotRequired[dict[str, int]]

    execution_reports: NotRequired[dict[str, dict[str, object]]]
    success_aliases: NotRequired[list[str]]
    failed_aliases: NotRequired[list[str]]
    failure_codes: NotRequired[list[str]]
    failure_details: NotRequired[list[dict[str, object]]]

    sql_pipeline_failure_stage: NotRequired[str]
    sql_pipeline_failure_details: NotRequired[list[dict[str, object]]]

    sql_answer_context: NotRequired[str]
    sql_plan: NotRequired[dict[str, object]]
    sql_result: NotRequired[dict[str, object]]

    assistant_message: str
