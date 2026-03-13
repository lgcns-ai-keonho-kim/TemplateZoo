"""
목적: LanceDB 엔진의 벡터 검색 동작을 검증한다.
설명: 로컬 LanceDB와 Ollama 임베딩을 사용해 벡터 검색 흐름을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/tool_proxy_agent/integrations/db/engines/lancedb/engine.py
"""

from __future__ import annotations

from typing import List

from tool_proxy_agent.integrations.db import DBClient
from tool_proxy_agent.integrations.db.base import Vector, VectorSearchRequest
from tool_proxy_agent.integrations.db.engines.lancedb import LanceDBEngine


def test_lancedb_engine_vector_search(tmp_path, ollama_embeddings) -> None:
    """LanceDB 벡터 검색(코사인 유사도 기반)을 검증한다."""

    embeddings = ollama_embeddings
    texts = ["고양이는 조용히 잠을 잔다.", "강아지는 산책을 좋아한다."]
    try:
        vectors = embeddings.embed_documents(texts)
        query_vector = embeddings.embed_query(texts[0])
    except Exception as error:  # noqa: BLE001 - 외부 의존 실패 대응
        raise RuntimeError(f"Ollama 임베딩 호출에 실패했습니다: {error}") from error
    if not vectors or not query_vector:
        raise RuntimeError("임베딩 결과가 비어 있습니다.")
    dimension = len(vectors[0])

    collection = _collection_name("vectors")
    uri = str(tmp_path / "lancedb")
    engine = LanceDBEngine(uri=uri)
    client = DBClient(engine)
    client.connect()
    client.create_collection(_collection_schema(collection, dimension=dimension))

    documents = [
        _doc("doc-1", {"text": texts[0]}, vector=vectors[0]),
        _doc("doc-2", {"text": texts[1]}, vector=vectors[1]),
    ]
    client.upsert(collection, documents)

    request = VectorSearchRequest(
        collection=collection,
        vector=Vector(values=query_vector),
        top_k=3,
    )
    response = client.vector_search(request)
    assert response.total >= 1
    assert response.results[0].document.doc_id == "doc-1"

    engine.delete_collection(collection)
    client.close()


def _collection_schema(name: str, dimension: int | None):
    from tool_proxy_agent.integrations.db.base import CollectionSchema

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
    from tool_proxy_agent.integrations.db.base import Document

    return Document(
        doc_id=doc_id,
        payload=payload,
        vector=None if vector is None else Vector(values=vector, dimension=len(vector)),
    )
