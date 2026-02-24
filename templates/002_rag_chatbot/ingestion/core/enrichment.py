"""
목적: ingestion 청크의 임베딩 생성을 담당한다.
설명: 임베딩 생성과 차원 계산 유틸을 제공한다.
디자인 패턴: 단계 보강 모듈
참조: ingestion/steps/embedding_step.py
"""

from __future__ import annotations

import re

from langchain_core.embeddings import Embeddings

from ingestion.core.types import IngestionChunk
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_TABLE_EMBEDDING_PATTERN = re.compile(
    r"\[TBL\].*?<SUMMARY>(?P<summary>.*?)</SUMMARY>.*?"
    r"<DESCRIPTION>(?P<description>.*?)</DESCRIPTION>.*?\[/TBL\]",
    flags=re.DOTALL,
)


def attach_embeddings(
    chunks: list[IngestionChunk],
    *,
    embedder: Embeddings,
) -> list[IngestionChunk]:
    """청크 본문 임베딩을 생성한다."""

    total = len(chunks)
    print(f"[진행][embedding] 임베딩 생성 시작: 총 청크 {total}개")
    progress_interval = max(1, total // 10) if total > 0 else 1
    for index, chunk in enumerate(chunks, start=1):
        embedding_source = _resolve_embedding_source_text(chunk.body)
        chunk.emb_body = [float(value) for value in embedder.embed_query(embedding_source)]
        if index % progress_interval == 0 or index == total:
            print(f"[진행][embedding] 처리 {index}/{total}")
    print("[진행][embedding] 임베딩 생성 완료")
    return chunks


def embedding_dimension(embedder: Embeddings) -> int:
    """임베더 차원을 계산한다."""

    vector = embedder.embed_query("embedding dimension probe")
    if not vector:
        detail = ExceptionDetail(
            code="INGESTION_EMBEDDING_EMPTY",
            cause="임베딩 벡터가 비어 있습니다.",
        )
        raise BaseAppException("임베딩 차원 계산에 실패했습니다.", detail)
    return len(vector)


def _resolve_embedding_source_text(body: str) -> str:
    """청크 본문 타입에 따라 임베딩 입력 텍스트를 선택한다."""

    matched = _TABLE_EMBEDDING_PATTERN.search(str(body or ""))
    if matched is None:
        return str(body or "")

    summary = _normalize_text(matched.group("summary"))
    description = _normalize_text(matched.group("description"))
    table_text = "\n\n".join(part for part in [summary, description] if part)
    if table_text:
        return table_text
    return str(body or "")


def _normalize_text(text: str) -> str:
    return " ".join(str(text or "").split()).strip()


__all__ = [
    "attach_embeddings",
    "embedding_dimension",
]
