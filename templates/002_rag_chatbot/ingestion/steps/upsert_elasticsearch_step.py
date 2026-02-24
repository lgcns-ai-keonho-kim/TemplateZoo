"""
목적: Elasticsearch 업서트 단계를 제공한다.
설명: ingestion 청크를 Elasticsearch rag_chunks 인덱스로 저장한다.
디자인 패턴: 단계 함수
참조: ingestion/core/db.py, ingestion/core/documents.py
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings

from ingestion.core.db import build_elasticsearch_schema, create_elasticsearch_client, ensure_collection
from ingestion.core.documents import batched, to_elasticsearch_documents
from ingestion.core.enrichment import embedding_dimension
from ingestion.core.types import IngestionChunk


def run_upsert_elasticsearch_step(
    chunks: list[IngestionChunk],
    *,
    embedder: Embeddings,
) -> None:
    """Elasticsearch 업서트를 수행한다."""

    if not chunks:
        print("[진행][upsert][elasticsearch] 업서트할 청크가 없습니다.")
        return

    embedding_dim = len(chunks[0].emb_body or [])
    if embedding_dim <= 0:
        embedding_dim = embedding_dimension(embedder)

    db_client = create_elasticsearch_client()
    schema = build_elasticsearch_schema(embedding_dim)
    ensure_collection(db_client, schema)

    documents = to_elasticsearch_documents(chunks)
    total_batches = max(1, (len(documents) + 99) // 100)
    print(
        f"[진행][upsert][elasticsearch] 업서트 시작: 문서 {len(documents)}개, "
        f"배치 {total_batches}개"
    )
    for batch_index, batch in enumerate(batched(documents, batch_size=100), start=1):
        db_client.upsert(schema.name, batch)
        print(
            f"[진행][upsert][elasticsearch] 배치 완료: {batch_index}/{total_batches} "
            f"(batch_size={len(batch)})"
        )
    print("[진행][upsert][elasticsearch] 업서트 완료")


__all__ = ["run_upsert_elasticsearch_step"]
