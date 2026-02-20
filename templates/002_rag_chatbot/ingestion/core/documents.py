"""
목적: ingestion 청크를 엔진별 업서트 문서로 변환한다.
설명: 공통 직렬화/검증/배치 분할과 SQLite·Postgres·Elasticsearch 매핑을 담당한다.
디자인 패턴: 어댑터 변환 모듈
참조: ingestion/steps/upsert_*.py
"""

from __future__ import annotations

import json
from typing import Iterator

from ingestion.core.types import IngestionChunk
from rag_chatbot.integrations.db.base import Document, Vector
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail


def to_sqlite_documents(chunks: list[IngestionChunk]) -> list[Document]:
    """SQLite-Vec 업서트 문서로 변환한다."""

    docs: list[Document] = []
    for chunk in chunks:
        _validate_file_name(chunk)
        docs.append(
            Document(
                doc_id=chunk.chunk_id,
                fields={
                    "index": chunk.index,
                    "file_name": chunk.file_name,
                    "file_path": chunk.file_path,
                    "body": chunk.body,
                    "metadata": _json_dumps(chunk.metadata),
                    "emb_body": _json_dumps(chunk.emb_body),
                },
                payload={},
                vector=Vector(values=chunk.emb_body or [], dimension=len(chunk.emb_body or [])),
            )
        )
    return docs


def to_postgres_documents(chunks: list[IngestionChunk]) -> list[Document]:
    """PostgreSQL(pgvector) 업서트 문서로 변환한다."""

    docs: list[Document] = []
    for chunk in chunks:
        _validate_file_name(chunk)
        docs.append(
            Document(
                doc_id=chunk.chunk_id,
                fields={
                    "index": chunk.index,
                    "file_name": chunk.file_name,
                    "file_path": chunk.file_path,
                    "body": chunk.body,
                    "metadata": _json_dumps(chunk.metadata),
                },
                payload={},
                vector=Vector(values=chunk.emb_body or [], dimension=len(chunk.emb_body or [])),
            )
        )
    return docs


def to_elasticsearch_documents(chunks: list[IngestionChunk]) -> list[Document]:
    """Elasticsearch 업서트 문서로 변환한다."""

    docs: list[Document] = []
    for chunk in chunks:
        _validate_file_name(chunk)
        docs.append(
            Document(
                doc_id=chunk.chunk_id,
                fields={
                    "index": chunk.index,
                    "file_name": chunk.file_name,
                    "file_path": chunk.file_path,
                    "body": chunk.body,
                    "metadata": chunk.metadata,
                },
                payload={},
                vector=Vector(values=chunk.emb_body or [], dimension=len(chunk.emb_body or [])),
            )
        )
    return docs


def batched(items: list[Document], batch_size: int = 100) -> Iterator[list[Document]]:
    """리스트를 배치 단위로 분할한다."""

    safe_batch_size = max(1, int(batch_size))
    for index in range(0, len(items), safe_batch_size):
        yield items[index : index + safe_batch_size]


def _json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _validate_file_name(chunk: IngestionChunk) -> None:
    if chunk.file_name.strip():
        return
    detail = ExceptionDetail(
        code="INGESTION_FILE_NAME_MISSING",
        cause=f"chunk_id={chunk.chunk_id}",
    )
    raise BaseAppException("file_name이 누락된 청크는 저장할 수 없습니다.", detail)


__all__ = [
    "to_sqlite_documents",
    "to_postgres_documents",
    "to_elasticsearch_documents",
    "batched",
]
