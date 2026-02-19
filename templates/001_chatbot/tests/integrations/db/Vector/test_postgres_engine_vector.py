"""
목적: PostgreSQL 엔진의 벡터 검색 동작을 검증한다.
설명: PGVector 확장이 준비된 환경에서 벡터 검색을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/postgres/engine.py
"""

from __future__ import annotations

import os
from typing import List

from base_template.integrations.db import DBClient
from base_template.integrations.db.base import Vector, VectorSearchRequest
from base_template.integrations.db.engines.postgres import PostgresEngine


def test_postgres_engine_vector_search(ollama_embeddings) -> None:
    """PostgreSQL 벡터 검색 동작을 검증한다."""

    params = _postgres_params()
    enable_vector = os.getenv("POSTGRES_ENABLE_VECTOR")
    if not params or not enable_vector:
        raise RuntimeError("POSTGRES_ENABLE_VECTOR 및 POSTGRES_* 환경 변수가 필요합니다.")

    embeddings = ollama_embeddings
    texts = ["커피 향이 진한 아침", "비 오는 날의 산책"]
    try:
        vectors = embeddings.embed_documents(texts)
        query_vector = embeddings.embed_query(texts[0])
    except Exception as exc:  # noqa: BLE001 - 외부 의존 실패 대응
        raise RuntimeError(f"Ollama 임베딩 호출에 실패했습니다: {exc}") from exc
    if not vectors or not query_vector:
        raise RuntimeError("임베딩 결과가 비어 있습니다.")
    dimension = len(vectors[0])

    engine = PostgresEngine(**params)
    client = DBClient(engine)
    client.connect()
    table = _collection_name("vectors")
    try:
        client.create_collection(_collection_schema(table, dimension=dimension))
    except Exception as error:
        engine.close()
        raise RuntimeError("PGVector 확장이 준비되지 않았습니다.") from error

    documents = [
        _doc("doc-1", {"text": texts[0]}, vector=vectors[0]),
        _doc("doc-2", {"text": texts[1]}, vector=vectors[1]),
    ]
    client.upsert(table, documents)

    request = VectorSearchRequest(
        collection=table,
        vector=Vector(values=query_vector),
        top_k=3,
    )
    response = client.vector_search(request)
    assert response.total >= 1

    engine.delete_collection(table)
    client.close()


def _collection_schema(name: str, dimension: int | None):
    from base_template.integrations.db.base import CollectionSchema

    return CollectionSchema(
        name=name,
        payload_field="payload",
        vector_field="embedding" if dimension else None,
        vector_dimension=dimension,
    )


def _collection_name(prefix: str) -> str:
    import uuid

    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _doc(doc_id: str, payload: dict, vector: List[float] | None = None):
    from base_template.integrations.db.base import Document

    return Document(
        doc_id=doc_id,
        payload=payload,
        vector=None if vector is None else Vector(values=vector, dimension=len(vector)),
    )


def _postgres_params() -> dict | None:
    dsn = os.getenv("POSTGRES_DSN")
    host = os.getenv("POSTGRES_HOST")
    port_raw = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PW")
    database = os.getenv("POSTGRES_DATABASE")
    if host and user and database:
        if not port_raw.isdigit():
            return None
        return {
            "host": host,
            "port": int(port_raw),
            "user": user,
            "password": password,
            "database": database,
        }
    if dsn:
        return {"dsn": dsn}
    return None
