"""
목적: SQLite 엔진의 벡터 검색 동작을 검증한다.
설명: sqlite-vec 확장을 사용해 벡터 검색 흐름을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/sqlite/engine.py
"""

from __future__ import annotations

from typing import List

from base_template.integrations.db import DBClient
from base_template.integrations.db.base import Vector, VectorSearchRequest
from base_template.integrations.db.engines.sqlite import SQLiteEngine


def test_sqlite_engine_vector_search(tmp_path, ollama_embeddings) -> None:
    """sqlite-vec가 설치된 경우 벡터 검색을 검증한다."""

    try:
        import sqlite_vec  # noqa: F401
    except ImportError as error:
        raise RuntimeError("sqlite-vec 패키지가 설치되어 있지 않습니다.") from error

    embeddings = ollama_embeddings
    texts = ["고양이는 조용히 잠을 잔다.", "강아지는 산책을 좋아한다."]
    try:
        vectors = embeddings.embed_documents(texts)
        query_vector = embeddings.embed_query(texts[0])
    except Exception as exc:  # noqa: BLE001 - 외부 의존 실패 대응
        raise RuntimeError(f"Ollama 임베딩 호출에 실패했습니다: {exc}") from exc
    if not vectors or not query_vector:
        raise RuntimeError("임베딩 결과가 비어 있습니다.")
    dimension = len(vectors[0])

    db_path = tmp_path / "vector.sqlite"
    engine = SQLiteEngine(str(db_path), enable_vector=True)
    client = DBClient(engine)
    client.connect()
    client.create_collection(_collection_schema("vectors", dimension=dimension))

    documents = [
        _doc("doc-1", {"text": texts[0]}, vector=vectors[0]),
        _doc("doc-2", {"text": texts[1]}, vector=vectors[1]),
    ]
    client.upsert("vectors", documents)

    request = VectorSearchRequest(
        collection="vectors",
        vector=Vector(values=query_vector),
        top_k=3,
    )
    response = client.vector_search(request)
    assert response.total >= 1
    assert response.results[0].document.doc_id == "doc-1"
    client.close()


def _collection_schema(name: str, dimension: int | None):
    from base_template.integrations.db.base import CollectionSchema

    return CollectionSchema(
        name=name,
        payload_field="payload",
        vector_field="embedding" if dimension else None,
        vector_dimension=dimension,
    )


def _doc(doc_id: str, payload: dict, vector: List[float] | None = None):
    from base_template.integrations.db.base import Document

    return Document(
        doc_id=doc_id,
        payload=payload,
        vector=None if vector is None else Vector(values=vector, dimension=len(vector)),
    )
