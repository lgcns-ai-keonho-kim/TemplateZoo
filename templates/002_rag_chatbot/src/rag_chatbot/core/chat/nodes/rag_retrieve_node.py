"""
목적: RAG 검색 노드를 제공한다.
설명: 질의 목록을 임베딩해 벡터 검색 원본 청크를 생성한다.
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
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import CollectionSchema, ColumnSpec, Vector, VectorSearchRequest
from rag_chatbot.integrations.db.engines.lancedb import LanceDBEngine
from rag_chatbot.shared.chat.nodes.function_node import function_node
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger

_DEFAULT_LANCEDB_URI = "data/db/vector"
_RAG_COLLECTION = "rag_chunks"
_BODY_TOP_K = 5


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

_rag_retrieve_embedder = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),
)


def _run_rag_retrieve_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """질의 목록 기반으로 벡터 검색 원본 청크를 생성한다."""

    # 1) 입력 질의 목록을 정규화하고 중복을 제거한다.
    #    - rag_queries가 있으면 우선 사용
    #    - 없으면 user_message를 fallback으로 사용
    #    - 같은 의미의 중복 질의(대소문자 차이)는 제거
    #    이 단계는 검색 품질보다도 "중복 API 호출 방지"가 핵심 목적이다.
    raw_queries = state.get("rag_queries")
    query_items = raw_queries if isinstance(raw_queries, list) else []
    normalized_queries: list[str] = []
    seen_queries: set[str] = set()

    for item in query_items:
        candidate = str(item or "").strip()
        lowered = candidate.lower()
        if candidate and lowered not in seen_queries:
            seen_queries.add(lowered)
            normalized_queries.append(candidate)

    user_query = str(state.get("user_message") or "").strip()
    if not normalized_queries and user_query:
        normalized_queries = [user_query]

    if not normalized_queries:
        detail = ExceptionDetail(
            code="RAG_QUERY_EMPTY",
            cause="rag_queries와 user_message가 모두 비어 있습니다.",
        )
        raise BaseAppException("RAG 검색 질의가 비어 있습니다.", detail)

    # 2) 정규화된 각 질의를 임베딩 벡터로 변환한다.
    #    OpenAI 임베딩 반환값(list[float])을 NumPy 배열로 받아 dtype을 명시하고
    #    다시 list로 변환해 저장한다.
    #    - dtype 고정: 값 표현 일관성 확보
    #    - list 복원: DB 요청 모델(Vector)이 기대하는 직렬화 형태 유지
    query_vectors = {
        query: np.asarray(
            _rag_retrieve_embedder.embed_query(query),
            dtype=np.float32,
        ).tolist()
        for query in normalized_queries
    }

    # 3) 질의 벡터를 DB 벡터 검색 요청 모델로 구성한다.
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

    # 4) LanceDB 검색 요청을 병렬 제출해 처리한다.
    search_responses = []
    with ThreadPoolExecutor(max_workers=max(1, len(search_requests))) as executor:
        futures = [
            executor.submit(_rag_retrieve_db_client.vector_search, request)
            for request in search_requests
        ]
        for future in as_completed(futures):
            search_responses.append(future.result())

    # 5) 검색 결과 문서를 그래프 상태 표준 청크 스키마로 정규화한다.
    #    엔진/인덱서에 따라 값이 fields 또는 payload에 들어올 수 있으므로
    #    "fields 우선, payload fallback" 규칙을 통일해 후속 노드의 입력 스키마를 고정한다.
    retrieved_chunks: list[RagRetrievedChunk] = []
    for response in search_responses:
        for result in response.results:
            document = result.document
            fields = getattr(document, "fields", {})
            payload = getattr(document, "payload", {})
            field_values = fields if isinstance(fields, dict) else {}
            payload_values = payload if isinstance(payload, dict) else {}

            raw_file_name = field_values.get("file_name", payload_values.get("file_name"))
            file_name = str(raw_file_name or "").strip()
            if not file_name:
                detail = ExceptionDetail(
                    code="RAG_DOCUMENT_INVALID",
                    cause="file_name 필드가 비어 있습니다.",
                )
                raise BaseAppException("RAG 검색 문서 형식이 올바르지 않습니다.", detail)

            raw_file_path = field_values.get("file_path", payload_values.get("file_path"))
            file_path = "" if raw_file_path is None else str(raw_file_path)

            raw_body = field_values.get("body", payload_values.get("body"))
            if isinstance(raw_body, str):
                body = raw_body
            elif raw_body is None:
                body = ""
            elif isinstance(raw_body, (int, float, bool)):
                body = str(raw_body)
            else:
                body = json.dumps(raw_body, ensure_ascii=False)

            raw_metadata = field_values.get("metadata", payload_values.get("metadata"))
            metadata: dict[str, Any] = {}
            if isinstance(raw_metadata, dict):
                metadata = raw_metadata
            elif isinstance(raw_metadata, str):
                # metadata가 문자열(JSON)로 저장된 케이스를 허용한다.
                # 파싱 실패 시 빈 dict로 두어 파이프라인을 중단하지 않는다.
                text = raw_metadata.strip()
                if text:
                    try:
                        decoded_metadata = json.loads(text)
                    except json.JSONDecodeError:
                        decoded_metadata = None
                    if isinstance(decoded_metadata, dict):
                        metadata = decoded_metadata

            raw_index = field_values.get("index", payload_values.get("index"))
            try:
                index_value = int(raw_index)
            except (TypeError, ValueError):
                index_value = 0

            score = float(result.score)

            retrieved_chunks.append(
                {
                    "chunk_id": str(document.doc_id),
                    "index": index_value,
                    "file_name": file_name,
                    "file_path": file_path,
                    "body": body,
                    "metadata": metadata,
                    "score": score,
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
            "RAG 검색 결과가 없습니다. `uv run python ingestion/ingest_lancedb.py --input-root data/ingestion-doc` 명령으로 데이터 적재를 먼저 수행하세요.",
            detail,
        )

    # 6) 최종 점수 순으로 정렬해 다음 노드 입력으로 전달한다.
    #    후속 dedup/top-k 노드는 "앞쪽일수록 우선순위가 높다"는 계약으로 동작하므로
    #    이 단계에서 정렬 기준을 단일화해 파이프라인 전반의 결정 일관성을 맞춘다.
    retrieved_chunks.sort(key=lambda item: float(item["score"]), reverse=True)
    _rag_retrieve_logger.info(
        "rag.retrieve.completed: queries=%s, retrieved_chunks=%s"
        % (len(normalized_queries), len(retrieved_chunks))
    )
    return {"rag_retrieved_chunks": retrieved_chunks}


rag_retrieve_node = function_node(
    fn=_run_rag_retrieve_step,
    node_name="rag_retrieve",
    logger=_rag_retrieve_logger,
)

__all__ = ["rag_retrieve_node", "RagRetrievedChunk"]
