"""
목적: RAG 랭킹 단계 내부 타입을 정의한다.
설명: 관련성 필터 결과와 인덱스 집합 타입을 제공한다.
디자인 패턴: 데이터 전송 객체(TypedDict)
참조: src/rag_chatbot/shared/chat/rags/functions/relevance_filter.py
"""

from __future__ import annotations

from typing import TypedDict

from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk


class RelevanceFilterResult(TypedDict):
    """관련성 필터 출력 타입."""

    stage: str
    lane: str
    selected_indexes: list[int]
    documents: list[RetrievedChunk]


__all__ = ["RelevanceFilterResult"]
