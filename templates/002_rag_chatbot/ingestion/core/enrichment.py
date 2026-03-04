"""
목적: ingestion 청크의 임베딩 생성을 담당한다.
설명: 비동기 배치 임베딩 생성, 표 요약 우선 임베딩, 차원 계산 유틸을 제공한다.
디자인 패턴: 단계 보강 모듈
참조: ingestion/steps/embedding_step.py
"""

from __future__ import annotations

import asyncio
import re

from langchain_core.embeddings import Embeddings

from ingestion.core.types import IngestionChunk
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_TABLE_EMBEDDING_PATTERN = re.compile(
    r"\[TBL\].*?<SUMMARY>(?P<summary>.*?)</SUMMARY>.*?"
    r"<DESCRIPTION>(?P<description>.*?)</DESCRIPTION>.*?\[/TBL\]",
    flags=re.DOTALL,
)
_ASYNC_EMBED_BATCH_SIZE = 32


def attach_embeddings(
    chunks: list[IngestionChunk],
    *,
    embedder: Embeddings,
) -> list[IngestionChunk]:
    """청크 본문 임베딩을 생성한다."""

    total = len(chunks)
    print(f"[진행][embedding] 임베딩 생성 시작: 총 청크 {total}개")
    if total <= 0:
        print("[진행][embedding] 임베딩 생성 완료")
        return chunks

    embedding_sources = [_resolve_embedding_source_text(chunk.body) for chunk in chunks]
    try:
        vectors = asyncio.run(
            _aembed_documents_in_batches(
                embedder=embedder,
                texts=embedding_sources,
                batch_size=_ASYNC_EMBED_BATCH_SIZE,
            )
        )
    except BaseAppException:
        raise
    except Exception as error:
        detail = ExceptionDetail(
            code="INGESTION_EMBEDDING_ASYNC_FAILED",
            cause=f"count={total}, error={error!s}",
        )
        raise BaseAppException("비동기 임베딩 생성에 실패했습니다.", detail) from None

    if len(vectors) != total:
        detail = ExceptionDetail(
            code="INGESTION_EMBEDDING_COUNT_MISMATCH",
            cause=f"expected={total}, actual={len(vectors)}",
        )
        raise BaseAppException("임베딩 결과 개수가 청크 개수와 다릅니다.", detail)

    progress_interval = max(1, total // 10)
    for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False), start=1):
        chunk.emb_body = [float(value) for value in vector]
        if index % progress_interval == 0 or index == total:
            print(f"[진행][embedding] 처리 {index}/{total}")

    print("[진행][embedding] 임베딩 생성 완료")
    return chunks


async def _aembed_documents_in_batches(
    *,
    embedder: Embeddings,
    texts: list[str],
    batch_size: int,
) -> list[list[float]]:
    """비동기 문서 임베딩을 배치 단위로 수행한다."""

    if not _supports_async_documents(embedder):
        detail = ExceptionDetail(
            code="INGESTION_EMBEDDER_ASYNC_UNSUPPORTED",
            cause=f"embedder={type(embedder).__name__}",
        )
        raise BaseAppException("현재 임베더는 비동기 문서 임베딩을 지원하지 않습니다.", detail)

    safe_batch_size = max(1, int(batch_size))
    vectors: list[list[float]] = []
    total = len(texts)
    done = 0
    for start in range(0, total, safe_batch_size):
        batch_texts = texts[start : start + safe_batch_size]
        batch_vectors = await embedder.aembed_documents(batch_texts)
        if len(batch_vectors) != len(batch_texts):
            detail = ExceptionDetail(
                code="INGESTION_EMBEDDING_BATCH_MISMATCH",
                cause=f"batch_expected={len(batch_texts)}, batch_actual={len(batch_vectors)}",
            )
            raise BaseAppException("비동기 임베딩 배치 결과 개수가 일치하지 않습니다.", detail)
        vectors.extend(batch_vectors)
        done += len(batch_texts)
        print(f"[진행][embedding] 비동기 배치 완료: {done}/{total}")
    return vectors


def _supports_async_documents(embedder: Embeddings) -> bool:
    """임베더의 비동기 문서 임베딩 지원 여부를 확인한다."""

    method = getattr(embedder, "aembed_documents", None)
    return callable(method)


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

    # 표 본문 전체 대신 요약/설명을 우선 임베딩해 의미 밀도를 높인다.
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
