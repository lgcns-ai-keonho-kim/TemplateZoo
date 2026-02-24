"""
목적: ingestion 임베딩 생성 단계를 제공한다.
설명: 청크 본문 텍스트에 대한 임베딩을 생성한다.
디자인 패턴: 단계 함수
참조: ingestion/core/enrichment.py
"""

from __future__ import annotations

from ingestion.core.enrichment import attach_embeddings, create_embedder
from ingestion.core.types import IngestionChunk


def run_embedding_step(chunks: list[IngestionChunk]) -> list[IngestionChunk]:
    """임베딩 생성 단계를 수행한다."""

    embedder = create_embedder()
    return attach_embeddings(chunks, embedder=embedder)


__all__ = ["run_embedding_step"]
