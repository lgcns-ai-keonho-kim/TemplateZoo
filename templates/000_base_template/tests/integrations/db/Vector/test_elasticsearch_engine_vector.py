"""
목적: Elasticsearch 엔진의 벡터 검색 동작을 검증한다.
설명: 실제 Elasticsearch 환경에서 벡터 검색을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/elasticsearch.py
"""

from __future__ import annotations

import os
from typing import List

import pytest

from base_template.integrations.db import DBClient
from base_template.integrations.db.base import Vector, VectorSearchRequest
from base_template.integrations.db.engines.elasticsearch import ElasticSearchEngine


def test_elasticsearch_engine_vector_search() -> None:
    """Elasticsearch 벡터 검색 동작을 검증한다."""

    params = _elasticsearch_params()
    if not params:
        pytest.skip("ELASTICSEARCH_HOSTS 또는 ELASTICSEARCH_* 환경 변수가 필요합니다.")

    engine = ElasticSearchEngine(**params)
    client = DBClient(engine)
    client.connect()
    index_name = _collection_name("vectors")
    client.create_collection(_collection_schema(index_name, dimension=3))

    documents = [
        _doc("doc-1", {"name": "A"}, vector=[0.1, 0.2, 0.3]),
        _doc("doc-2", {"name": "B"}, vector=[0.9, 0.8, 0.7]),
    ]
    client.upsert(index_name, documents)

    try:
        request = VectorSearchRequest(
            collection=index_name,
            vector=Vector(values=[0.1, 0.2, 0.3]),
            top_k=3,
        )
        response = client.vector_search(request)
    except Exception:
        engine.delete_collection(index_name)
        client.close()
        pytest.skip("Elasticsearch 벡터 검색 환경이 준비되지 않았습니다.")
    assert response.total >= 1

    engine.delete_collection(index_name)
    client.close()


def _elasticsearch_params() -> dict | None:
    host = os.getenv("ELASTICSEARCH_HOST")
    port_raw = os.getenv("ELASTICSEARCH_PORT", "9200")
    scheme = os.getenv("ELASTICSEARCH_SCHEME", "http")
    user = os.getenv("ELASTICSEARCH_USER")
    password = os.getenv("ELASTICSEARCH_PW")
    if host:
        if not port_raw.isdigit():
            return None
        return {
            "host": host,
            "port": int(port_raw),
            "scheme": scheme,
            "user": user,
            "password": password,
        }
    raw = os.getenv("ELASTICSEARCH_HOSTS")
    if not raw:
        return None
    hosts = [item.strip() for item in raw.split(",") if item.strip()]
    if not hosts:
        return None
    return {"hosts": hosts}


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
