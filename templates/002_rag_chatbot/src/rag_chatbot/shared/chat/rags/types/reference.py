"""
목적: RAG references 출력 타입을 정의한다.
설명: UI 전송용 references 구조를 일관되게 표현한다.
디자인 패턴: 데이터 전송 객체(TypedDict)
참조: src/rag_chatbot/shared/chat/rags/functions/format.py
"""

from __future__ import annotations

from typing import Literal, TypedDict


class RagReferenceMetadata(TypedDict, total=False):
    """RAG reference 메타데이터 타입."""

    index: int
    file_name: str
    file_path: str
    page_nums: list[int]
    score: float
    snippet: str


class RagReference(TypedDict):
    """RAG reference 아이템 타입."""

    type: Literal["reference"]
    content: str
    metadata: RagReferenceMetadata


__all__ = ["RagReference", "RagReferenceMetadata"]
