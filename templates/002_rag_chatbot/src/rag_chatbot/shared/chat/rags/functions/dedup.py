"""
목적: RAG 결과 중복 제거 함수를 제공한다.
설명: chunk_id 및 file_name+page_num 기준 중복 제거를 수행한다.
디자인 패턴: 함수형 유틸
참조: src/rag_chatbot/shared/chat/rags/types/retrieval.py
"""

from __future__ import annotations

from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk


def merge_by_chunk_id(docs: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """chunk_id 기준으로 중복을 제거하고 최대 점수를 유지한다."""

    bucket: dict[str, RetrievedChunk] = {}
    for doc in docs:
        key = doc["chunk_id"]
        existing = bucket.get(key)
        if existing is None:
            bucket[key] = doc
            continue
        if doc["score"] > existing["score"]:
            bucket[key] = doc
            continue
        if doc["source"] != existing["source"]:
            existing["source"] = "merged"
    merged = list(bucket.values())
    merged.sort(key=lambda item: item["score"], reverse=True)
    return merged


def dedup_by_file_page(docs: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """file_name + metadata.page_num 기준으로 중복 제거한다."""

    bucket: dict[str, RetrievedChunk] = {}
    for doc in docs:
        metadata = doc.get("metadata") or {}
        page_num = metadata.get("page_num") if isinstance(metadata, dict) else None
        if page_num is None:
            page_num = doc.get("index")
        key = f"{doc.get('file_name', '')}::{page_num}"
        current = bucket.get(key)
        if current is None or doc["score"] > current["score"]:
            bucket[key] = doc
    deduped = list(bucket.values())
    deduped.sort(key=lambda item: item["score"], reverse=True)
    return deduped


__all__ = ["merge_by_chunk_id", "dedup_by_file_page"]
