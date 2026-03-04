"""
목적: RAG 검색 노드를 제공한다.
설명: 질의 목록을 임베딩해 벡터 검색 원본 청크(`rag_retrieved_chunks`)를 생성한다.
      최종 `rag_context`/`rag_references` 생성은 rag_format 노드에서 수행한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/rag_chatbot/shared/chat/nodes/function_node.py, src/rag_chatbot/core/chat/nodes/rag_chunk_dedup_node.py
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Literal, TypedDict

import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import (
    CollectionSchema,
    ColumnSpec,
    Pagination,
    Query,
    Vector,
    VectorSearchRequest,
)
from rag_chatbot.integrations.db.engines.lancedb import LanceDBEngine
from rag_chatbot.integrations.embedding import EmbeddingClient
from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.config import resolve_gemini_embedding_dim
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger

_DEFAULT_LANCEDB_URI = "data/db/vector"
_RAG_COLLECTION = "rag_chunks"
_BODY_TOP_K = 5
_RAG_EMBEDDING_DIM = resolve_gemini_embedding_dim()


class RagRetrievedChunk(TypedDict):
    """검색 원본 청크 타입."""

    chunk_id: str
    index: int
    file_name: str
    file_path: str
    body: str
    metadata: dict[str, Any]
    score: float
    source: Literal["body", "merged"]
    snippet: str


_rag_retrieve_schema = CollectionSchema(
    name=_RAG_COLLECTION,
    primary_key="chunk_id",
    payload_field=None,
    vector_field="emb_body",
    vector_dimension=_RAG_EMBEDDING_DIM,
    columns=[
        ColumnSpec(name="chunk_id", data_type="TEXT", is_primary=True),
        ColumnSpec(name="index", data_type="INTEGER"),
        ColumnSpec(name="file_name", data_type="TEXT", nullable=False),
        ColumnSpec(name="file_path", data_type="TEXT", nullable=False),
        ColumnSpec(name="body", data_type="TEXT", nullable=False),
        ColumnSpec(name="metadata", data_type="TEXT"),
        ColumnSpec(name="emb_body", is_vector=True, dimension=_RAG_EMBEDDING_DIM),
    ],
)

_rag_retrieve_logger: Logger = create_default_logger("RagRetrieveNode")
_lancedb_uri = str(os.getenv("LANCEDB_URI", _DEFAULT_LANCEDB_URI)).strip() or _DEFAULT_LANCEDB_URI
if "://" not in _lancedb_uri:
    Path(_lancedb_uri).mkdir(parents=True, exist_ok=True)
_lancedb_engine = LanceDBEngine(
    uri=_lancedb_uri,
    logger=_rag_retrieve_logger,
)
_rag_retrieve_db_client = DBClient(_lancedb_engine)
_rag_retrieve_db_client.register_schema(_rag_retrieve_schema)
_rag_retrieve_db_client.connect()
_rag_retrieve_db_client.create_collection(_rag_retrieve_schema)

_rag_retrieve_embedder = EmbeddingClient(
    model=GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", ""),
        project=os.getenv("GEMINI_PROJECT", ""),
        output_dimensionality=_RAG_EMBEDDING_DIM,
    ),
    name="rag-retrieve-embedding",
)


def _validate_existing_rag_vector_dimension() -> None:
    """RAG 컬렉션 기존 벡터 차원이 현재 설정과 호환되는지 검증한다."""

    documents = _rag_retrieve_db_client.fetch(
        _RAG_COLLECTION,
        Query(pagination=Pagination(limit=1, offset=0)),
    )
    if not documents:
        return

    vector = documents[0].vector.values if documents[0].vector is not None else []
    if not vector:
        detail = ExceptionDetail(
            code="RAG_EMBEDDING_VECTOR_MISSING",
            cause=f"collection={_RAG_COLLECTION}, doc_id={documents[0].doc_id}",
        )
        raise BaseAppException("RAG 저장소의 기존 벡터를 확인할 수 없습니다.", detail)

    existing_dim = len(vector)
    if existing_dim == _RAG_EMBEDDING_DIM:
        return

    detail = ExceptionDetail(
        code="RAG_EMBEDDING_DIMENSION_MISMATCH",
        cause=(
            "벡터 차원 불일치: "
            f"collection={_RAG_COLLECTION}, expected_dim={_RAG_EMBEDDING_DIM}, existing_dim={existing_dim}"
        ),
    )
    raise BaseAppException(
        "RAG 검색 벡터 차원이 ingestion 차원과 다릅니다. ingestion을 다시 실행해 벡터 저장소를 재구성하세요.",
        detail,
    )


_validate_existing_rag_vector_dimension()


def _run_rag_retrieve_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """질의 목록 기반으로 벡터 검색 원본 청크를 생성한다."""

    # 현재 그래프에서는 rag_keyword_postprocess_node가 rag_queries를 보장한다.
    # 따라서 이 노드는 rag_queries만 입력으로 받는 단일 경로로 유지한다.
    raw_queries = state.get("rag_queries")
    if not isinstance(raw_queries, list):
        detail = ExceptionDetail(
            code="RAG_QUERY_EMPTY",
            cause="rag_queries가 비어 있거나 리스트가 아닙니다.",
        )
        raise BaseAppException("RAG 검색 질의가 비어 있습니다.", detail)

    normalized_queries: list[str] = []
    seen_queries: set[str] = set()
    for item in raw_queries:
        query = str(item or "").strip()
        if not query:
            continue
        key = query.lower()
        if key in seen_queries:
            continue
        seen_queries.add(key)
        normalized_queries.append(query)

    if not normalized_queries:
        detail = ExceptionDetail(
            code="RAG_QUERY_EMPTY",
            cause="rag_queries에서 유효한 질의를 찾지 못했습니다.",
        )
        raise BaseAppException("RAG 검색 질의가 비어 있습니다.", detail)

    # 질의 임베딩은 단건 순차 호출 대신 배치 호출로 생성한다.
    # (embed_query N회 -> embed_documents 1회)
    query_vectors = _build_query_vectors(normalized_queries)

    search_requests = [
        VectorSearchRequest(
            collection=_RAG_COLLECTION,
            vector=Vector(values=query_vectors[query], dimension=len(query_vectors[query])),
            top_k=max(1, int(_BODY_TOP_K)),
            include_vectors=False,
            vector_field="emb_body",
        )
        for query in normalized_queries
    ]

    # 검색은 질의별 병렬 처리로 latency를 줄인다.
    search_responses = []
    with ThreadPoolExecutor(max_workers=max(1, len(search_requests))) as executor:
        futures = [
            executor.submit(_rag_retrieve_db_client.vector_search, request)
            for request in search_requests
        ]
        for future in as_completed(futures):
            search_responses.append(future.result())

    # 결과 정규화는 document.fields 기준의 단일 스키마만 사용한다.
    retrieved_chunks: list[RagRetrievedChunk] = []
    for response in search_responses:
        for result in response.results:
            document = result.document
            fields = document.fields if isinstance(document.fields, dict) else {}

            chunk_id = str(document.doc_id or "").strip()
            file_name = str(fields.get("file_name") or "").strip()
            body = str(fields.get("body") or "")
            if not chunk_id or not file_name or not body.strip():
                detail = ExceptionDetail(
                    code="RAG_DOCUMENT_INVALID",
                    cause="chunk_id/file_name/body 필수 필드가 비어 있습니다.",
                )
                raise BaseAppException("RAG 검색 문서 형식이 올바르지 않습니다.", detail)

            file_path = str(fields.get("file_path") or "")

            raw_metadata = fields.get("metadata")
            metadata: dict[str, Any] = {}
            if isinstance(raw_metadata, dict):
                metadata = raw_metadata
            elif isinstance(raw_metadata, str):
                text = raw_metadata.strip()
                if text:
                    try:
                        decoded_metadata = json.loads(text)
                    except json.JSONDecodeError:
                        decoded_metadata = None
                    if isinstance(decoded_metadata, dict):
                        metadata = decoded_metadata

            try:
                index_value = int(fields.get("index") or 0)
            except (TypeError, ValueError):
                index_value = 0

            retrieved_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "index": index_value,
                    "file_name": file_name,
                    "file_path": file_path,
                    "body": body,
                    "metadata": metadata,
                    "score": float(result.score),
                    "source": "body",
                    "snippet": body[:240],
                }
            )

    if not retrieved_chunks:
        detail = ExceptionDetail(
            code="RAG_RETRIEVE_EMPTY",
            cause="rag_chunks 컬렉션에 검색 결과가 없습니다.",
        )
        raise BaseAppException(
            "RAG 검색 결과가 없습니다.",
            detail,
        )

    retrieved_chunks.sort(key=lambda item: float(item["score"]), reverse=True)
    _rag_retrieve_logger.info(
        "rag.retrieve.completed: queries=%s, retrieved_chunks=%s"
        % (len(normalized_queries), len(retrieved_chunks))
    )
    return {"rag_retrieved_chunks": retrieved_chunks}


def _build_query_vectors(queries: list[str]) -> dict[str, list[float]]:
    """RAG 질의 목록의 임베딩 벡터를 배치로 생성한다."""

    try:
        vectors = _rag_retrieve_embedder.embed_documents(queries)
    except BaseAppException:
        raise
    except Exception as error:
        detail = ExceptionDetail(
            code="RAG_QUERY_EMBED_FAILED",
            cause=f"query_count={len(queries)}, error={error!s}",
        )
        raise BaseAppException("RAG 질의 임베딩 생성에 실패했습니다.", detail) from None

    if len(vectors) != len(queries):
        detail = ExceptionDetail(
            code="RAG_QUERY_EMBED_COUNT_MISMATCH",
            cause=f"expected={len(queries)}, actual={len(vectors)}",
        )
        raise BaseAppException("RAG 질의 임베딩 결과 개수가 일치하지 않습니다.", detail)

    query_vectors: dict[str, list[float]] = {}
    for query, vector in zip(queries, vectors, strict=True):
        query_vectors[query] = np.asarray(vector, dtype=np.float32).tolist()
    return query_vectors


rag_retrieve_node = function_node(
    fn=_run_rag_retrieve_step,
    node_name="rag_retrieve",
    logger=_rag_retrieve_logger,
)

__all__ = ["rag_retrieve_node", "RagRetrievedChunk"]
