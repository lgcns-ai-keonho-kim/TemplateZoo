"""
목적: PostgreSQL(pgvector) 업서트 단계를 제공한다.
설명: ingestion 청크를 PostgreSQL rag_chunks 테이블로 저장한다.
디자인 패턴: 단계 함수
참조: ingestion/core/db.py, ingestion/core/documents.py
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings

from ingestion.core.db import (
    build_postgres_schema,
    create_postgres_client,
    ensure_collection,
    validate_existing_vector_dimension,
)
from ingestion.core.documents import batched, to_postgres_documents
from ingestion.core.enrichment import embedding_dimension
from ingestion.core.types import IngestionChunk


def run_upsert_postgres_step(
    chunks: list[IngestionChunk],
    *,
    embedder: Embeddings,
    reset: bool = False,
) -> None:
    """PostgreSQL(pgvector) 업서트를 수행한다."""

    if not chunks:
        print("[진행][upsert][postgres] 업서트할 청크가 없습니다.")
        return

    embedding_dim = len(chunks[0].emb_body or [])
    if embedding_dim <= 0:
        embedding_dim = embedding_dimension(embedder)

    db_client = create_postgres_client()
    schema = build_postgres_schema(embedding_dim)
    if reset:
        print(
            f"[진행][upsert][postgres] --reset 활성화: 기존 테이블 삭제 후 재생성 "
            f"(collection={schema.name})"
        )
        db_client.connect()
        db_client.delete_collection(schema.name)
    ensure_collection(db_client, schema)
    validate_existing_vector_dimension(
        db_client,
        schema=schema,
        expected_dim=embedding_dim,
    )

    documents = to_postgres_documents(chunks)
    total_batches = max(1, (len(documents) + 99) // 100)
    print(
        f"[진행][upsert][postgres] 업서트 시작: 문서 {len(documents)}개, "
        f"배치 {total_batches}개"
    )
    for batch_index, batch in enumerate(batched(documents, batch_size=100), start=1):
        db_client.upsert(schema.name, batch)
        print(
            f"[진행][upsert][postgres] 배치 완료: {batch_index}/{total_batches} "
            f"(batch_size={len(batch)})"
        )
    print("[진행][upsert][postgres] 업서트 완료")


__all__ = ["run_upsert_postgres_step"]
