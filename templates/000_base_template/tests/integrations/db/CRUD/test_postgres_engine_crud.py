"""
목적: PostgreSQL 엔진의 기본 CRUD 동작을 검증한다.
설명: 실제 PostgreSQL 환경에서 테이블/문서 작업을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/postgres.py
"""

from __future__ import annotations

import logging
import os
import pytest

from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.postgres import PostgresEngine


_LOGGER = logging.getLogger("tests.crud")


def _log_step(action: str, **context) -> None:
    """CRUD 단계별 동작을 로깅한다."""

    if context:
        payload = ", ".join(f"{key}={value}" for key, value in context.items())
        _LOGGER.info("%s | %s", action, payload)
        return
    _LOGGER.info("%s", action)


def test_postgres_engine_basic_crud() -> None:
    """PostgreSQL CRUD 기본 동작을 검증한다."""

    params = _postgres_params()
    if not params:
        pytest.skip("POSTGRES_DSN 또는 POSTGRES_* 환경 변수가 필요합니다.")

    _log_step("엔진 생성", mode="direct" if "dsn" not in params else "dsn")
    engine = PostgresEngine(**params)
    _log_step("클라이언트 생성")
    client = DBClient(engine)
    _log_step("연결 시작")
    client.connect()
    table = _collection_name("items")
    _log_step("컬렉션 생성", name=table)
    client.create_collection(_collection_schema(table, dimension=None))

    _log_step("문서 저장", doc_id="doc-1")
    client.upsert(table, [_doc("doc-1", {"status": "ACTIVE"})])
    _log_step("문서 조회", doc_id="doc-1")
    loaded = engine.get(table, "doc-1")
    assert loaded is not None
    assert loaded.payload["status"] == "ACTIVE"

    _log_step("조건 조회", field="status", op="eq", value="ACTIVE")
    docs = client.read(table).where("status").eq("ACTIVE").fetch()
    assert len(docs) >= 1

    _log_step("문서 삭제", doc_id="doc-1")
    engine.delete(table, "doc-1")
    _log_step("컬렉션 삭제", name=table)
    engine.delete_collection(table)
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


def _collection_name(prefix: str) -> str:
    import uuid

    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _doc(doc_id: str, payload: dict):
    from base_template.integrations.db.base import Document

    return Document(doc_id=doc_id, payload=payload, vector=None)


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
