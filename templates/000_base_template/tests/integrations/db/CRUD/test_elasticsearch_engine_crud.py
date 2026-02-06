"""
목적: Elasticsearch 엔진의 기본 CRUD 동작을 검증한다.
설명: 실제 Elasticsearch 환경에서 인덱스/문서 작업을 확인한다.
디자인 패턴: 테스트 케이스
참조: src/base_template/integrations/db/engines/elasticsearch/engine.py
"""

from __future__ import annotations

import logging
import os

import pytest

from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.elasticsearch import ElasticSearchEngine


_LOGGER = logging.getLogger("tests.crud")


def _log_step(action: str, **context) -> None:
    """CRUD 단계별 동작을 로깅한다."""

    if context:
        payload = ", ".join(f"{key}={value}" for key, value in context.items())
        _LOGGER.info("%s | %s", action, payload)
        return
    _LOGGER.info("%s", action)


def test_elasticsearch_engine_basic_crud() -> None:
    """Elasticsearch CRUD 기본 동작을 검증한다."""

    params = _elasticsearch_params()
    if not params:
        pytest.skip("ELASTICSEARCH_HOSTS 또는 ELASTICSEARCH_* 환경 변수가 필요합니다.")

    _log_step("엔진 생성", mode="direct" if "hosts" not in params else "hosts")
    engine = ElasticSearchEngine(**params)
    _log_step("클라이언트 생성")
    client = DBClient(engine)
    _log_step("연결 시작")
    client.connect()
    index_name = _collection_name("items")
    _log_step("컬렉션 생성", name=index_name)
    client.create_collection(_collection_schema(index_name, dimension=None))

    _log_step("문서 저장", doc_id="doc-1")
    client.upsert(index_name, [_doc("doc-1", {"status": "ACTIVE"})])
    _log_step("인덱스 리프레시", name=index_name)
    engine.refresh_collection(index_name)
    _log_step("문서 조회", doc_id="doc-1")
    loaded = engine.get(index_name, "doc-1")
    assert loaded is not None
    assert loaded.payload["status"] == "ACTIVE"

    _log_step("조건 조회", field="status", op="eq", value="ACTIVE")
    docs = client.read(index_name).where("status").eq("ACTIVE").fetch()
    assert len(docs) >= 1

    _log_step("문서 삭제", doc_id="doc-1")
    engine.delete(index_name, "doc-1")
    _log_step("컬렉션 삭제", name=index_name)
    engine.delete_collection(index_name)
    _log_step("연결 종료")
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
