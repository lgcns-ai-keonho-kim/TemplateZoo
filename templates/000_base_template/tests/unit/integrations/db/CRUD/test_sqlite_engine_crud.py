"""
목적: SQLite 엔진의 기본 CRUD 동작을 검증한다.
설명: sqlite-vec 비활성화 상태에서 테이블 CRUD 흐름을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/sqlite.py
"""

from __future__ import annotations

import logging

from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.sqlite import SqliteVectorEngine


_LOGGER = logging.getLogger("tests.crud")


def _log_step(action: str, **context) -> None:
    """CRUD 단계별 동작을 로깅한다."""

    if context:
        payload = ", ".join(f"{key}={value}" for key, value in context.items())
        _LOGGER.info("%s | %s", action, payload)
        return
    _LOGGER.info("%s", action)


def test_sqlite_engine_basic_crud(tmp_path) -> None:
    """SQLite CRUD 기본 동작을 검증한다."""

    db_path = tmp_path / "test.sqlite"
    _log_step("엔진 생성", db_path=db_path)
    engine = SqliteVectorEngine(str(db_path), enable_vector=False)
    _log_step("클라이언트 생성")
    client = DBClient(engine)
    _log_step("연결 시작")
    client.connect()
    _log_step("컬렉션 생성", name="items")
    client.create_collection(_collection_schema("items", dimension=None))

    _log_step("문서 저장", doc_id="doc-1")
    client.upsert("items", [_doc("doc-1", {"status": "ACTIVE"})])
    _log_step("문서 조회", doc_id="doc-1")
    loaded = engine.get("items", "doc-1")
    assert loaded is not None
    assert loaded.payload["status"] == "ACTIVE"

    _log_step("조건 조회", field="status", op="eq", value="ACTIVE")
    docs = client.read("items").where("status").eq("ACTIVE").fetch()
    assert len(docs) == 1

    _log_step("문서 삭제", doc_id="doc-1")
    engine.delete("items", "doc-1")
    _log_step("삭제 확인", doc_id="doc-1")
    assert engine.get("items", "doc-1") is None
    _log_step("컬렉션 삭제", name="items")
    engine.delete_collection("items")
    _log_step("연결 종료")
    client.close()


def _collection_schema(name: str, dimension: int | None):
    from base_template.integrations.db.base import CollectionSchema

    return CollectionSchema(
        name=name,
        payload_field="payload",
        vector_field="embedding" if dimension else None,
        vector_dimension=dimension,
    )


def _doc(doc_id: str, payload: dict):
    from base_template.integrations.db.base import Document

    return Document(doc_id=doc_id, payload=payload, vector=None)
