"""
목적: Chat LangGraph 상태 타입을 정의한다.
설명: 그래프 실행 시 입력/출력으로 전달되는 최소 상태 구조를 제공한다.
디자인 패턴: 상태 객체(State Object)
참조: src/rag_chatbot/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from typing_extensions import Annotated, NotRequired, TypedDict

from rag_chatbot.core.chat.models import ChatMessage


def _merge_relevance_judge_results(
    left: list[dict[str, object]],
    right: list[dict[str, object]],
) -> list[dict[str, object]]:
    """관련성 판정 결과 목록을 누적 병합한다."""

    # 빈 리스트는 "현재 배치 결과 초기화" 신호로 사용한다.
    if not right:
        return []
    return [*left, *right]


class ChatGraphState(TypedDict):
    """LangGraph 대화 상태 타입."""

    session_id: str
    user_message: str
    history: list[ChatMessage]
    safeguard_result: NotRequired[str]
    safeguard_route: NotRequired[str]
    context_strategy: NotRequired[str]
    context_strategy_raw: NotRequired[str]
    last_assistant_message: NotRequired[str]
    safeguard_reason: NotRequired[str]
    rag_keyword_raw: NotRequired[str]
    rag_queries: NotRequired[list[str]]
    rag_retrieved_chunks: NotRequired[list[dict[str, object]]]
    rag_candidates: NotRequired[list[dict[str, object]]]
    rag_relevance_batch_id: NotRequired[str]
    rag_relevance_judge_inputs: NotRequired[list[dict[str, object]]]
    rag_relevance_candidate_index: NotRequired[int]
    rag_relevance_candidate: NotRequired[dict[str, object]]
    rag_relevance_judge_results: NotRequired[
        Annotated[list[dict[str, object]], _merge_relevance_judge_results]
    ]
    rag_relevance_passed_docs: NotRequired[list[dict[str, object]]]
    rag_relevance_raw: NotRequired[str]
    rag_file_page_deduped_docs: NotRequired[list[dict[str, object]]]
    rag_filtered_docs: NotRequired[list[dict[str, object]]]
    rag_context: NotRequired[str]
    rag_references: NotRequired[list[dict[str, object]]]
    assistant_message: str
