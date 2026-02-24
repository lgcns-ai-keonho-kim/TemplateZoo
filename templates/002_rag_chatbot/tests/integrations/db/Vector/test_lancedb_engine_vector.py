"""
목적: LanceDB 엔진의 벡터 검색 동작을 검증한다.
설명: 수동 벡터 데이터를 기준으로 업서트/검색/필터/벡터 제외 옵션을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/rag_chatbot/integrations/db/engines/lancedb/engine.py
"""

from __future__ import annotations

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import (
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    FilterCondition,
    FilterExpression,
    FilterOperator,
    Vector,
    VectorSearchRequest,
)
from rag_chatbot.integrations.db.engines.lancedb import LanceDBEngine


def test_lancedb_engine_vector_search(tmp_path) -> None:
    """LanceDB 벡터 검색 기본 동작을 검증한다."""

    engine = LanceDBEngine(uri=str(tmp_path / "lancedb"))
    client = DBClient(engine)
    client.connect()

    schema = _collection_schema("vectors", dimension=3)
    client.create_collection(schema)

    documents = [
        _doc("doc-1", "ACTIVE", "고양이 문서", [0.1, 0.2, 0.3]),
        _doc("doc-2", "INACTIVE", "강아지 문서", [0.9, 0.1, 0.0]),
        _doc("doc-3", "ACTIVE", "새 문서", [0.1, 0.2, 0.25]),
    ]
    client.upsert("vectors", documents)

    response = client.vector_search(
        VectorSearchRequest(
            collection="vectors",
            vector=Vector(values=[0.1, 0.2, 0.3], dimension=3),
            top_k=2,
            include_vectors=False,
        )
    )
    assert response.total == 2
    assert response.results[0].document.doc_id == "doc-1"
    assert response.results[0].document.vector is None

    filtered = client.vector_search(
        VectorSearchRequest(
            collection="vectors",
            vector=Vector(values=[0.1, 0.2, 0.3], dimension=3),
            top_k=3,
            include_vectors=True,
            filter_expression=FilterExpression(
                conditions=[
                    FilterCondition(
                        field="status",
                        source=FieldSource.COLUMN,
                        operator=FilterOperator.EQ,
                        value="ACTIVE",
                    )
                ],
                logic="AND",
            ),
        )
    )
    assert filtered.total == 2
    assert {item.document.doc_id for item in filtered.results} == {"doc-1", "doc-3"}
    assert all(item.document.vector is not None for item in filtered.results)

    client.close()


def _collection_schema(name: str, dimension: int) -> CollectionSchema:
    return CollectionSchema(
        name=name,
        primary_key="doc_id",
        payload_field="payload",
        vector_field="embedding",
        vector_dimension=dimension,
        columns=[
            ColumnSpec(name="doc_id", data_type="TEXT", is_primary=True),
            ColumnSpec(name="status", data_type="TEXT"),
            ColumnSpec(name="text", data_type="TEXT"),
            ColumnSpec(name="embedding", is_vector=True, dimension=dimension),
        ],
    )


def _doc(doc_id: str, status: str, text: str, vector_values: list[float]) -> Document:
    return Document(
        doc_id=doc_id,
        fields={"status": status, "text": text},
        payload={"status": status},
        vector=Vector(values=vector_values, dimension=len(vector_values)),
    )
