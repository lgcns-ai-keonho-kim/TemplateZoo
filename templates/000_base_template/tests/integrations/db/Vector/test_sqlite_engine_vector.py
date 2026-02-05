"""
목적: SQLite 엔진의 벡터 검색 동작을 검증한다.
설명: sqlite-vec 확장을 사용해 벡터 검색 흐름을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/sqlite.py
"""

from __future__ import annotations

from typing import List

import pytest

from base_template.integrations.db import DBClient
from base_template.integrations.db.base import Vector, VectorSearchRequest
from base_template.integrations.db.engines.sqlite import SqliteVectorEngine


def test_sqlite_engine_vector_search(tmp_path) -> None:
    """sqlite-vec가 설치된 경우 벡터 검색을 검증한다."""

    sqlite_vec = pytest.importorskip("sqlite_vec")
    if sqlite_vec is None:
        pytest.skip("sqlite-vec가 설치되지 않았습니다.")

    db_path = tmp_path / "vector.sqlite"
    engine = SqliteVectorEngine(str(db_path), enable_vector=True)
    client = DBClient(engine)
    client.connect()
    client.create_collection(_collection_schema("vectors", dimension=3))

    documents = [
        _doc("doc-1", {"name": "A"}, vector=[0.1, 0.2, 0.3]),
        _doc("doc-2", {"name": "B"}, vector=[0.9, 0.8, 0.7]),
    ]
    client.upsert("vectors", documents)

    request = VectorSearchRequest(
        collection="vectors",
        vector=Vector(values=[0.1, 0.2, 0.3]),
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
