"""
목적: Elasticsearch 엔진의 벡터 검색 동작을 검증한다.
설명: 실제 Elasticsearch 환경에서 벡터 검색을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/chatbot/integrations/db/engines/elasticsearch/engine.py
"""

from __future__ import annotations

import os
from typing import List

from chatbot.integrations.db import DBClient
from chatbot.integrations.db.base import Vector, VectorSearchRequest
from chatbot.integrations.db.engines.elasticsearch import ElasticsearchEngine


def test_elasticsearch_engine_vector_search(ollama_embeddings) -> None:
    """Elasticsearch 벡터 검색 동작을 검증한다."""

    params = _elasticsearch_params()
    if not params:
        raise RuntimeError("ELASTICSEARCH_HOSTS 또는 ELASTICSEARCH_* 환경 변수가 필요합니다.")

    embeddings = ollama_embeddings
    texts = ["도시에 내리는 비", "시골의 고요한 밤"]
    try:
        vectors = embeddings.embed_documents(texts)
        query_vector = embeddings.embed_query(texts[0])
    except Exception as exc:  # noqa: BLE001 - 외부 의존 실패 대응
        raise RuntimeError(f"Ollama 임베딩 호출에 실패했습니다: {exc}") from exc
    if not vectors or not query_vector:
        raise RuntimeError("임베딩 결과가 비어 있습니다.")
    dimension = len(vectors[0])

    engine = ElasticsearchEngine(**params)
    client = DBClient(engine)
    client.connect()
    index_name = _collection_name("vectors")
    client.create_collection(_collection_schema(index_name, dimension=dimension))

    documents = [
        _doc("doc-1", {"text": texts[0]}, vector=vectors[0]),
        _doc("doc-2", {"text": texts[1]}, vector=vectors[1]),
    ]
    client.upsert(index_name, documents)
    engine.refresh_collection(index_name)

    try:
        request = VectorSearchRequest(
            collection=index_name,
            vector=Vector(values=query_vector),
            top_k=3,
        )
        response = client.vector_search(request)
    except Exception:
        engine.delete_collection(index_name)
        client.close()
        raise RuntimeError("Elasticsearch 벡터 검색 환경이 준비되지 않았습니다.")
    assert response.total >= 1

    engine.delete_collection(index_name)
    client.close()


def _elasticsearch_params() -> dict | None:
    host = os.getenv("ELASTICSEARCH_HOST")
    port_raw = os.getenv("ELASTICSEARCH_PORT", "9200")
    scheme = os.getenv("ELASTICSEARCH_SCHEME", "http")
    user = os.getenv("ELASTICSEARCH_USER")
    password = os.getenv("ELASTICSEARCH_PW")
    ca_certs = os.getenv("ELASTICSEARCH_CA_CERTS")
    verify_certs = _parse_bool(os.getenv("ELASTICSEARCH_VERIFY_CERTS"))
    ssl_fingerprint = os.getenv("ELASTICSEARCH_SSL_FINGERPRINT")
    if host:
        if not port_raw.isdigit():
            return None
        params = {
            "host": host,
            "port": int(port_raw),
            "scheme": scheme,
            "user": user,
            "password": password,
            "ca_certs": ca_certs,
            "verify_certs": verify_certs,
            "ssl_assert_fingerprint": ssl_fingerprint,
        }
        return _drop_none(params)
    raw = os.getenv("ELASTICSEARCH_HOSTS")
    if not raw:
        return None
    hosts = [item.strip() for item in raw.split(",") if item.strip()]
    if not hosts:
        return None
    params = {
        "hosts": hosts,
        "ca_certs": ca_certs,
        "verify_certs": verify_certs,
        "ssl_assert_fingerprint": ssl_fingerprint,
    }
    return _drop_none(params)


def _parse_bool(value: str | None) -> bool | None:
    """문자열을 bool로 변환한다."""

    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _drop_none(params: dict) -> dict:
    """None 값 파라미터를 제거한다."""

    return {key: value for key, value in params.items() if value is not None}


def _collection_schema(name: str, dimension: int | None):
    from chatbot.integrations.db.base import CollectionSchema

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
    from chatbot.integrations.db.base import Document

    return Document(
        doc_id=doc_id,
        payload=payload,
        vector=None if vector is None else Vector(values=vector, dimension=len(vector)),
    )
