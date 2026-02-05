"""
목적: Redis 엔진의 기본 CRUD 동작을 검증한다.
설명: 실제 Redis 환경에서 문서 저장/조회/삭제 흐름을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/redis.py
"""

from __future__ import annotations

import logging
import os
import pytest

from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.redis import RedisEngine


_LOGGER = logging.getLogger("tests.crud")


def _log_step(action: str, **context) -> None:
    """CRUD 단계별 동작을 로깅한다."""

    if context:
        payload = ", ".join(f"{key}={value}" for key, value in context.items())
        _LOGGER.info("%s | %s", action, payload)
        return
    _LOGGER.info("%s", action)


def test_redis_engine_basic_crud() -> None:
    """Redis CRUD 기본 동작을 검증한다."""

    params = _redis_params()
    if not params:
        pytest.skip("REDIS_URL 또는 REDIS_* 환경 변수가 필요합니다.")

    _log_step("엔진 생성", mode="direct" if "url" not in params else "url", vector="disabled")
    engine = RedisEngine(**params, enable_vector=False)
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
    assert len(docs) == 1

    _log_step("문서 삭제", doc_id="doc-1")
    engine.delete(collection, "doc-1")
    _log_step("삭제 확인", doc_id="doc-1")
    assert engine.get(collection, "doc-1") is None
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


def _redis_params() -> dict | None:
    url = os.getenv("REDIS_URL")
    host = os.getenv("REDIS_HOST")
    port_raw = os.getenv("REDIS_PORT", "6379")
    db_raw = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PW")
    if host:
        if not port_raw.isdigit() or not db_raw.isdigit():
            return None
        return {
            "host": host,
            "port": int(port_raw),
            "db": int(db_raw),
            "password": password,
        }
    if url:
        return {"url": url}
    return None
