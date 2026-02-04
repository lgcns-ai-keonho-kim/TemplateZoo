"""
목적: Redis 엔진의 벡터 검색 동작을 검증한다.
설명: 실제 Redis 환경에서 벡터 검색을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/redis.py
"""

from __future__ import annotations

import os
from typing import List

import pytest

from base_template.integrations.db import DBClient
from base_template.integrations.db.base import Vector
from base_template.integrations.db.engines.redis import RedisEngine


def test_redis_engine_vector_search() -> None:
    """Redis 벡터 검색(코사인 유사도 기반)을 검증한다."""

    params = _redis_params()
    if not params:
        pytest.skip("REDIS_URL 또는 REDIS_* 환경 변수가 필요합니다.")

    engine = RedisEngine(**params, enable_vector=True)
    client = DBClient(engine)
    client.connect()
    collection = _collection_name("vectors")
    client.create_collection(_collection_schema(collection, dimension=3))

    documents = [
        _doc("doc-1", {"name": "A"}, vector=[0.1, 0.2, 0.3]),
        _doc("doc-2", {"name": "B"}, vector=[0.9, 0.8, 0.7]),
    ]
    client.upsert(collection, documents)

    response = (
        client.read(collection)
        .vector([0.1, 0.2, 0.3])
        .top_k(3)
        .fetch_vector()
    )
    assert response.total >= 1
    assert response.results[0].document.doc_id == "doc-1"

    engine.delete_collection(collection)
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


def _redis_params() -> dict | None:
    url = os.getenv("REDIS_URL")
    host = os.getenv("REDIS_HOST")
    port_raw = os.getenv("REDIS_PORT", "6379")
    db_raw = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PW")
    if host:
        if not port_raw.isdigit() or not db_raw.isdigit():
            return None
        return {
            "host": host,
            "port": int(port_raw),
            "db": int(db_raw),
            "password": password,
        }
    if url:
        return {"url": url}
    return None
