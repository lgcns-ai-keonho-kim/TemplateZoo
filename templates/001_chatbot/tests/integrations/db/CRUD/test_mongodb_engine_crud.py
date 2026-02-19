"""
목적: MongoDB 엔진의 기본 CRUD 동작을 검증한다.
설명: 실제 MongoDB 환경에서 컬렉션/문서 작업을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/mongodb/engine.py
"""

from __future__ import annotations

import logging
import os

from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.mongodb import MongoDBEngine


_LOGGER = logging.getLogger("tests.crud")


def _log_step(action: str, **context) -> None:
    """CRUD 단계별 동작을 로깅한다."""

    if context:
        payload = ", ".join(f"{key}={value}" for key, value in context.items())
        _LOGGER.info("%s | %s", action, payload)
        return
    _LOGGER.info("%s", action)


def test_mongodb_engine_basic_crud() -> None:
    """MongoDB CRUD 기본 동작을 검증한다."""

    params = _mongodb_params()
    if not params:
        raise RuntimeError("MONGODB_DB 또는 MONGODB_* 환경 변수가 필요합니다.")

    _log_step("엔진 생성", mode="direct" if "uri" not in params else "uri")
    engine = MongoDBEngine(**params)
    _log_step("클라이언트 생성")
    client = DBClient(engine)
    _log_step("연결 시작")
    client.connect()
    collection = _collection_name("items")
    _log_step("컬렉션 생성", name=collection)
    client.create_collection(_collection_schema(collection, dimension=None))

    _log_step("문서 저장", doc_id="doc-1")
    client.upsert(collection, [_doc("doc-1", {"status": "ACTIVE"})])
    _log_step("문서 조회", doc_id="doc-1")
    loaded = engine.get(collection, "doc-1")
    assert loaded is not None
    assert loaded.payload["status"] == "ACTIVE"

    _log_step("조건 조회", field="status", op="eq", value="ACTIVE")
    docs = client.read(collection).where("status").eq("ACTIVE").fetch()
    assert len(docs) >= 1

    _log_step("문서 삭제", doc_id="doc-1")
    engine.delete(collection, "doc-1")
    _log_step("컬렉션 삭제", name=collection)
    engine.delete_collection(collection)
    _log_step("연결 종료")
    client.close()


def test_mongodb_engine_query_dsl() -> None:
    """MongoDB에서 DSL 기반 일반 조회 동작을 검증한다."""

    params = _mongodb_params()
    if not params:
        raise RuntimeError("MONGODB_DB 또는 MONGODB_* 환경 변수가 필요합니다.")

    _log_step("엔진 생성", mode="direct" if "uri" not in params else "uri")
    engine = MongoDBEngine(**params)
    _log_step("클라이언트 생성")
    client = DBClient(engine)
    _log_step("연결 시작")
    client.connect()
    collection = _collection_name("query")
    _log_step("컬렉션 생성", name=collection)
    client.create_collection(_collection_schema(collection, dimension=None))

    documents = [
        _doc("doc-1", {"status": "ACTIVE", "score": 10}),
        _doc("doc-2", {"status": "INACTIVE", "score": 5}),
        _doc("doc-3", {"status": "ACTIVE", "score": 15}),
    ]
    _log_step("문서 배치 저장", count=len(documents))
    client.upsert(collection, documents)

    _log_step("조건 조회", field="status", op="eq", value="ACTIVE")
    _log_step("조건 조회", field="score", op="gte", value=10)
    docs = (
        client.read(collection)
        .where("status")
        .eq("ACTIVE")
        .where("score")
        .gte(10)
        .fetch()
    )
    assert len(docs) == 2

    _log_step("컬렉션 삭제", name=collection)
    engine.delete_collection(collection)
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


def _mongodb_params() -> dict | None:
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB")
    auth_db = os.getenv("MONGODB_AUTH_DB") or None
    host = os.getenv("MONGODB_HOST")
    port_raw = os.getenv("MONGODB_PORT", "27017")
    user = os.getenv("MONGODB_USER")
    password = os.getenv("MONGODB_PW")
    if not db_name:
        return None
    if host:
        if not port_raw.isdigit():
            return None
        return {
            "database": db_name,
            "host": host,
            "port": int(port_raw),
            "user": user,
            "password": password,
            "auth_source": auth_db,
        }
    if uri:
        params = {"uri": uri, "database": db_name, "auth_source": auth_db}
        return _drop_none(params)
    return None


def _drop_none(params: dict) -> dict:
    """None 값 파라미터를 제거한다."""

    return {key: value for key, value in params.items() if value is not None}
