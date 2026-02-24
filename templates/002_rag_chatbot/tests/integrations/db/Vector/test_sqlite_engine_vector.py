"""
목적: SQLite 엔진의 벡터 비지원 정책을 검증한다.
설명: SQLite를 RDB 전용으로 고정했을 때 벡터 경로가 명시 오류를 반환하는지 확인한다.
디자인 패턴: 테스트 케이스
참조: src/rag_chatbot/integrations/db/engines/sqlite/engine.py
"""

from __future__ import annotations

import pytest

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import CollectionSchema, Vector, VectorSearchRequest
from rag_chatbot.integrations.db.engines.sqlite import SQLiteEngine


def test_sqlite_engine_rejects_vector_schema_on_register(tmp_path) -> None:
    """SQLite 엔진은 벡터 스키마 등록을 허용하지 않아야 한다."""

    engine = SQLiteEngine(str(tmp_path / "vector.sqlite"))
    client = DBClient(engine)
    client.connect()

    with pytest.raises(RuntimeError, match="벡터"):
        client.register_schema(_vector_schema("vectors", dimension=3))

    client.close()


def test_sqlite_engine_vector_search_is_disabled(tmp_path) -> None:
    """SQLite 엔진의 vector_search 호출은 명시 오류여야 한다."""

    engine = SQLiteEngine(str(tmp_path / "vector.sqlite"))
    engine.connect()
    request = VectorSearchRequest(
        collection="vectors",
        vector=Vector(values=[0.1, 0.2, 0.3], dimension=3),
        top_k=3,
    )

    with pytest.raises(RuntimeError, match="벡터 검색"):
        engine.vector_search(request, _vector_schema("vectors", dimension=3))

    engine.close()


def _vector_schema(name: str, dimension: int):
    return CollectionSchema(
        name=name,
        payload_field="payload",
        vector_field="embedding",
        vector_dimension=dimension,
    )
