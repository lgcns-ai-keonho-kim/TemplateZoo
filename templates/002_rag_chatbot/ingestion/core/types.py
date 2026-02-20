"""
목적: ingestion 공통 타입과 상수를 정의한다.
설명: 청크 데이터 모델과 컬렉션 상수를 단일 책임으로 관리한다.
디자인 패턴: 데이터 모델 모듈
참조: ingestion/steps/*.py
"""

from __future__ import annotations

from dataclasses import dataclass

RAG_COLLECTION = "rag_chunks"


@dataclass
class IngestionChunk:
    """ingestion 중간 산출물 청크 모델."""

    chunk_id: str
    index: int
    file_name: str
    file_path: str
    body: str
    metadata: dict[str, object]
    emb_body: list[float] | None


__all__ = ["IngestionChunk", "RAG_COLLECTION"]
