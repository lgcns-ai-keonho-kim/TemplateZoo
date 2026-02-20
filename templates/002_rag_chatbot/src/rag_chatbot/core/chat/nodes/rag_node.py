"""
목적: RAG 노드 조립체를 제공한다.
설명: DB/LLM/임베더 런타임을 모듈 레벨에서 구성하고, 그래프에서 바로 사용할 `rag_node` 인스턴스를 노출한다.
디자인 패턴: 모듈 조립
참조: src/rag_chatbot/core/chat/graphs/chat_graph.py, src/rag_chatbot/shared/chat/nodes/rag_node.py
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

from rag_chatbot.shared.chat.nodes.rag_node import RagNode
from rag_chatbot.core.chat.prompts.rags import (
    KEYWORD_GENERATION_PROMPT,
    RELEVANCE_FILTER_PROMPT,
)
from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import CollectionSchema, ColumnSpec
from rag_chatbot.integrations.db.engines.sqlite import SQLiteEngine
from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.logging import Logger, create_default_logger

_RAG_COLLECTION = "rag_chunks"

# RAG 기본 스키마 등록
_rag_schema = CollectionSchema(
    name=_RAG_COLLECTION,
    primary_key="chunk_id",
    payload_field=None,
    vector_field="emb_body",
    columns=[
        ColumnSpec(name="chunk_id", data_type="TEXT", is_primary=True),
        ColumnSpec(name="index", data_type="INTEGER"),
        ColumnSpec(name="file_name", data_type="TEXT", nullable=False),
        ColumnSpec(name="file_path", data_type="TEXT", nullable=False),
        ColumnSpec(name="body", data_type="TEXT", nullable=False),
        ColumnSpec(name="metadata", data_type="TEXT"),
        ColumnSpec(name="emb_body", is_vector=True, dimension=1536),
    ],
)

_rag_logger: Logger = create_default_logger("RagNodeRuntime")

# 기본 런타임: SQLite-Vec
_sqlite_path = Path(os.getenv("SQLITE_DB_PATH", "data/db/playground.sqlite"))
_sqlite_path.parent.mkdir(parents=True, exist_ok=True)
_sqlite_engine = SQLiteEngine(
    database_path=str(_sqlite_path),
    logger=_rag_logger,
    enable_vector=True,
)
_rag_db_client = DBClient(_sqlite_engine)
_rag_db_client.register_schema(_rag_schema)
_rag_db_client.connect()
_rag_db_client.create_collection(_rag_schema)

# 아래는 대체 조립 예시다. 필요 시 기본 조립을 교체해서 사용한다.
# ----------------------------------------------------------------
# PostgreSQL(pgvector) 버전:
# from rag_chatbot.integrations.db.engines.postgres import PostgresEngine
# _postgres_engine = PostgresEngine(
#     dsn=(os.getenv("POSTGRES_DSN") or "").strip() or None,
#     host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
#     port=int(os.getenv("POSTGRES_PORT", "5432")),
#     user=os.getenv("POSTGRES_USER", "postgres"),
#     password=(os.getenv("POSTGRES_PW") or "").strip() or None,
#     database=os.getenv("POSTGRES_DATABASE", "playground"),
#     logger=_rag_logger,
# )
# _rag_db_client = DBClient(_postgres_engine)
# _rag_db_client.register_schema(_rag_schema)
# _rag_db_client.connect()
#
# Elasticsearch 버전:
# from rag_chatbot.integrations.db.engines.elasticsearch import ElasticsearchEngine
# _elastic_hosts = (os.getenv("ELASTICSEARCH_HOSTS") or "").strip()
# _elastic_engine = ElasticsearchEngine(
#     hosts=[item.strip() for item in _elastic_hosts.split(",") if item.strip()] or None,
#     scheme=os.getenv("ELASTICSEARCH_SCHEME", "http"),
#     host=os.getenv("ELASTICSEARCH_HOST", "127.0.0.1"),
#     port=int(os.getenv("ELASTICSEARCH_PORT", "9200")),
#     user=(os.getenv("ELASTICSEARCH_USER") or "").strip() or None,
#     password=(os.getenv("ELASTICSEARCH_PW") or "").strip() or None,
#     ca_certs=(os.getenv("ELASTICSEARCH_CA_CERTS") or "").strip() or None,
#     verify_certs=(os.getenv("ELASTICSEARCH_VERIFY_CERTS", "true").strip().lower() == "true"),
#     ssl_assert_fingerprint=(os.getenv("ELASTICSEARCH_SSL_FINGERPRINT") or "").strip() or None,
#     logger=_rag_logger,
# )
# _rag_db_client = DBClient(_elastic_engine)
# _rag_db_client.register_schema(_rag_schema)
# _rag_db_client.connect()
# ----------------------------------------------------------------

_rag_model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", ""),
    api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),
)
_rag_llm_client = LLMClient(model=_rag_model, name="chat-rag-llm")

_rag_embedder = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

rag_node = RagNode(
    db_client=_rag_db_client,
    llm_client=_rag_llm_client,
    embedder=_rag_embedder,
    collection=_RAG_COLLECTION,
    max_generated_keywords=5,
    body_top_k=5,
    relevance_filter_top_k=20,
    final_top_k=8,
    reference_fields=None,
    metadata_fields=None,
    enable_llm=True,
    keyword_generation_prompt=KEYWORD_GENERATION_PROMPT,
    relevance_filter_prompt=RELEVANCE_FILTER_PROMPT,
    logger=_rag_logger,
)

__all__ = ["rag_node"]
