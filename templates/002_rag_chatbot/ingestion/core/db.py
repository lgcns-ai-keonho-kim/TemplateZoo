"""
목적: ingestion 단계의 DB 클라이언트/스키마 생성을 담당한다.
설명: 엔진별 클라이언트 구성과 공통 컬렉션 스키마 정의를 제공한다.
디자인 패턴: 팩토리 + 스키마 빌더 모듈
참조: ingestion/steps/upsert_*.py
"""

from __future__ import annotations

import os

from ingestion.core.types import RAG_COLLECTION
from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import CollectionSchema, ColumnSpec
from rag_chatbot.integrations.db.engines.elasticsearch import ElasticsearchEngine
from rag_chatbot.integrations.db.engines.postgres import PostgresEngine
from rag_chatbot.integrations.db.engines.sqlite import SQLiteEngine
from rag_chatbot.shared.logging import Logger, create_default_logger


def create_logger(name: str = "Ingestion") -> Logger:
    """ingestion 전용 로거를 생성한다."""

    return create_default_logger(name)


def create_sqlite_client(logger: Logger | None = None) -> DBClient:
    """SQLite-Vec 기본 DBClient를 생성한다."""

    engine = SQLiteEngine(
        database_path=os.getenv("SQLITE_DB_PATH", "data/db/playground.sqlite"),
        logger=logger,
        enable_vector=True,
    )
    return DBClient(engine)


def create_postgres_client(logger: Logger | None = None) -> DBClient:
    """PostgreSQL(pgvector) DBClient를 생성한다."""

    engine = PostgresEngine(
        dsn=(os.getenv("POSTGRES_DSN") or "").strip() or None,
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=(os.getenv("POSTGRES_PW") or "").strip() or None,
        database=os.getenv("POSTGRES_DATABASE", "playground"),
        logger=logger,
    )
    return DBClient(engine)


def create_elasticsearch_client(logger: Logger | None = None) -> DBClient:
    """Elasticsearch DBClient를 생성한다."""

    hosts_raw = (os.getenv("ELASTICSEARCH_HOSTS") or "").strip()
    hosts = [item.strip() for item in hosts_raw.split(",") if item.strip()] or None
    verify_raw = os.getenv("ELASTICSEARCH_VERIFY_CERTS", "true").strip().lower()
    engine = ElasticsearchEngine(
        hosts=hosts,
        scheme=os.getenv("ELASTICSEARCH_SCHEME", "http"),
        host=os.getenv("ELASTICSEARCH_HOST", "127.0.0.1"),
        port=int(os.getenv("ELASTICSEARCH_PORT", "9200")),
        user=(os.getenv("ELASTICSEARCH_USER") or "").strip() or None,
        password=(os.getenv("ELASTICSEARCH_PW") or "").strip() or None,
        ca_certs=(os.getenv("ELASTICSEARCH_CA_CERTS") or "").strip() or None,
        verify_certs=verify_raw == "true",
        ssl_assert_fingerprint=(os.getenv("ELASTICSEARCH_SSL_FINGERPRINT") or "").strip() or None,
        logger=logger,
    )
    return DBClient(engine)


def build_sqlite_schema(embedding_dim: int) -> CollectionSchema:
    """SQLite-Vec ingestion 스키마를 생성한다."""

    return CollectionSchema(
        name=RAG_COLLECTION,
        primary_key="chunk_id",
        payload_field=None,
        vector_field="emb_body",
        vector_dimension=embedding_dim,
        columns=[
            ColumnSpec(name="chunk_id", data_type="TEXT", is_primary=True),
            ColumnSpec(name="index", data_type="INTEGER"),
            ColumnSpec(name="file_name", data_type="TEXT", nullable=False),
            ColumnSpec(name="file_path", data_type="TEXT", nullable=False),
            ColumnSpec(name="body", data_type="TEXT", nullable=False),
            ColumnSpec(name="metadata", data_type="TEXT"),
            ColumnSpec(name="emb_body", data_type="TEXT", is_vector=True, dimension=embedding_dim),
        ],
    )


def build_postgres_schema(embedding_dim: int) -> CollectionSchema:
    """PostgreSQL(pgvector) ingestion 스키마를 생성한다."""

    return CollectionSchema(
        name=RAG_COLLECTION,
        primary_key="chunk_id",
        payload_field=None,
        vector_field="emb_body",
        vector_dimension=embedding_dim,
        columns=[
            ColumnSpec(name="chunk_id", data_type="TEXT", is_primary=True),
            ColumnSpec(name="index", data_type="INTEGER"),
            ColumnSpec(name="file_name", data_type="TEXT", nullable=False),
            ColumnSpec(name="file_path", data_type="TEXT", nullable=False),
            ColumnSpec(name="body", data_type="TEXT", nullable=False),
            ColumnSpec(name="metadata", data_type="TEXT"),
            ColumnSpec(name="emb_body", is_vector=True, dimension=embedding_dim),
        ],
    )


def build_elasticsearch_schema(embedding_dim: int) -> CollectionSchema:
    """Elasticsearch ingestion 스키마를 생성한다."""

    return CollectionSchema(
        name=RAG_COLLECTION,
        primary_key="chunk_id",
        payload_field=None,
        vector_field="emb_body",
        vector_dimension=embedding_dim,
        columns=[
            ColumnSpec(name="chunk_id", data_type="keyword", is_primary=True),
            ColumnSpec(name="index", data_type="integer"),
            ColumnSpec(name="file_name", data_type="keyword", nullable=False),
            ColumnSpec(name="file_path", data_type="keyword", nullable=False),
            ColumnSpec(name="body", data_type="text", nullable=False),
            ColumnSpec(name="metadata", data_type="object"),
            ColumnSpec(name="emb_body", is_vector=True, dimension=embedding_dim),
        ],
    )


def ensure_collection(db_client: DBClient, schema: CollectionSchema) -> None:
    """컬렉션 스키마를 보장한다."""

    db_client.connect()
    db_client.register_schema(schema)
    db_client.create_collection(schema)


__all__ = [
    "create_logger",
    "create_sqlite_client",
    "create_postgres_client",
    "create_elasticsearch_client",
    "build_sqlite_schema",
    "build_postgres_schema",
    "build_elasticsearch_schema",
    "ensure_collection",
]
