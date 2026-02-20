"""
목적: RAG 벡터 검색 함수를 제공한다.
설명: 쿼리 임베딩 생성 후 body 벡터 필드를 병렬 검색한다.
디자인 패턴: 함수형 파이프라인
참조: src/rag_chatbot/shared/chat/rags/types/retrieval.py
"""

from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import Vector, VectorSearchRequest
from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail


def search_parallel(
    queries: list[str],
    *,
    db_client: DBClient,
    collection: str,
    embed_query: Callable[[str], list[float]],
    body_top_k: int,
) -> list[RetrievedChunk]:
    """유저 쿼리 + 확장 쿼리를 병렬로 검색한다."""

    normalized_queries = _normalize_queries(queries)
    if not normalized_queries:
        return []

    query_vectors = {query: embed_query(query) for query in normalized_queries}
    body_docs: list[RetrievedChunk] = []

    futures = {}
    with ThreadPoolExecutor(max_workers=max(1, len(normalized_queries))) as executor:
        for query in normalized_queries:
            vector = query_vectors[query]
            futures[
                executor.submit(
                    _search_by_field,
                    db_client=db_client,
                    collection=collection,
                    vector=vector,
                    top_k=body_top_k,
                )
            ] = None

        for future in as_completed(futures):
            docs = future.result()
            body_docs.extend(docs)

    return _dedup_by_chunk_id(body_docs)


def _search_by_field(
    *,
    db_client: DBClient,
    collection: str,
    vector: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    request = VectorSearchRequest(
        collection=collection,
        vector=Vector(values=vector, dimension=len(vector)),
        top_k=max(1, int(top_k)),
        include_vectors=False,
        vector_field="emb_body",
    )
    response = db_client.vector_search(request)

    engine_name = str(getattr(db_client.engine, "name", "")).strip().lower()
    chunks: list[RetrievedChunk] = []
    for result in response.results:
        document = result.document
        score = _normalize_score(engine_name, float(result.score))

        file_name = _string_field(document, "file_name")
        if not file_name:
            detail = ExceptionDetail(
                code="RAG_DOCUMENT_INVALID",
                cause="file_name 필드가 비어 있습니다.",
            )
            raise BaseAppException("RAG 검색 문서 형식이 올바르지 않습니다.", detail)

        body = _string_field(document, "body")
        metadata = _dict_field(document, "metadata")

        raw_index = _raw_field(document, "index")
        try:
            index_value = int(raw_index)
        except (TypeError, ValueError):
            index_value = 0

        chunk_id = str(document.doc_id)
        file_path = _string_field(document, "file_path")

        chunks.append(
            {
                "chunk_id": chunk_id,
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

    chunks.sort(key=lambda item: item["score"], reverse=True)
    return chunks


def _normalize_score(engine_name: str, raw_score: float) -> float:
    if engine_name in {"sqlite", "postgres"}:
        if raw_score < 0:
            raw_score = 0.0
        return 1.0 / (1.0 + raw_score)
    return raw_score


def _dedup_by_chunk_id(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    bucket: dict[str, RetrievedChunk] = {}
    for chunk in chunks:
        key = chunk["chunk_id"]
        current = bucket.get(key)
        if current is None or chunk["score"] > current["score"]:
            bucket[key] = chunk
    deduped = list(bucket.values())
    deduped.sort(key=lambda item: item["score"], reverse=True)
    return deduped


def _normalize_queries(queries: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in queries:
        candidate = str(item or "").strip()
        if not candidate:
            continue
        lowered = candidate.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(candidate)
    return normalized


def _raw_field(document: Any, field: str) -> Any:
    fields = getattr(document, "fields", {})
    if isinstance(fields, dict) and field in fields:
        return fields[field]
    payload = getattr(document, "payload", {})
    if isinstance(payload, dict) and field in payload:
        return payload[field]
    return None


def _string_field(document: Any, field: str) -> str:
    raw = _raw_field(document, field)
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, (int, float, bool)):
        return str(raw)
    return json.dumps(raw, ensure_ascii=False)


def _dict_field(document: Any, field: str) -> dict[str, Any]:
    raw = _raw_field(document, field)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if isinstance(decoded, dict):
            return decoded
    return {}


__all__ = ["search_parallel"]
