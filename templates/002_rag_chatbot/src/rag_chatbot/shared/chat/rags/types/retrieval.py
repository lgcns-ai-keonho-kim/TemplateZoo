"""
목적: RAG 검색 단계 내부 타입을 정의한다.
설명: 검색 후보 청크 타입을 제공한다.
디자인 패턴: 데이터 전송 객체(TypedDict)
참조: src/rag_chatbot/shared/chat/rags/functions/retrieve.py
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


class RetrievedChunk(TypedDict):
    """검색 결과 청크 타입."""

    chunk_id: str
    index: int
    file_name: str
    file_path: str
    body: str
    metadata: dict[str, Any]
    score: float
    source: Literal["body", "merged"]
    snippet: NotRequired[str]


__all__ = ["RetrievedChunk"]
