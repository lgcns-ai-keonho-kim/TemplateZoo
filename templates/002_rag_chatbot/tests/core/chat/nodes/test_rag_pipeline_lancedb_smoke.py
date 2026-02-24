"""
목적: LanceDB 실데이터 기준 RAG 기본 파이프라인 동작을 검증한다.
설명: ingestion으로 적재된 `rag_chunks`를 읽어 질의를 만들고, retrieve -> dedup -> top-k -> format 흐름이 실제로 동작하는지 확인한다.
디자인 패턴: 스모크 테스트(실환경 의존)
참조: src/rag_chatbot/core/chat/nodes/rag_retrieve_node.py, src/rag_chatbot/core/chat/nodes/rag_chunk_dedup_node.py, src/rag_chatbot/core/chat/nodes/rag_file_page_dedup_node.py, src/rag_chatbot/core/chat/nodes/rag_final_topk_node.py, src/rag_chatbot/core/chat/nodes/rag_format_node.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from rag_chatbot.core.chat.nodes.rag_chunk_dedup_node import rag_chunk_dedup_node
from rag_chatbot.core.chat.nodes.rag_file_page_dedup_node import rag_file_page_dedup_node
from rag_chatbot.core.chat.nodes.rag_final_topk_node import rag_final_topk_node
from rag_chatbot.core.chat.nodes.rag_format_node import rag_format_node
from rag_chatbot.core.chat.nodes.rag_retrieve_node import rag_retrieve_node


def _read_query_seed_from_lancedb(uri: str) -> str:
    """LanceDB `rag_chunks`에서 질의 시드 본문을 1건 가져온다."""

    try:
        import lancedb
    except ImportError as error:
        raise RuntimeError("lancedb 패키지가 설치되어 있지 않습니다.") from error

    safe_uri = uri.strip() or "data/db/vector"
    if "://" not in safe_uri and not Path(safe_uri).exists():
        raise RuntimeError(f"LanceDB 경로가 존재하지 않습니다: {safe_uri}")

    database = lancedb.connect(safe_uri)
    list_result = database.list_tables()
    table_names = list_result if isinstance(list_result, list) else getattr(list_result, "tables", [])
    if "rag_chunks" not in table_names:
        raise RuntimeError("rag_chunks 컬렉션이 없습니다. ingestion을 먼저 실행해주세요.")

    table = database.open_table("rag_chunks")
    rows = (
        table.search()
        .where("body IS NOT NULL AND body != ''")
        .select(["body"])
        .limit(1)
        .to_arrow()
        .to_pylist()
    )
    if not rows:
        raise RuntimeError("rag_chunks에 본문 데이터가 없습니다. ingestion을 먼저 실행해주세요.")

    body = str(rows[0].get("body") or "").strip()
    if not body:
        raise RuntimeError("rag_chunks 본문이 비어 있습니다.")
    return body[:120]


@pytest.mark.asyncio
async def test_rag_pipeline_smoke_with_existing_lancedb_data() -> None:
    """실데이터 기준으로 RAG 검색/정제/포맷 파이프라인이 기본 동작해야 한다."""

    openai_api_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY 환경 변수가 필요합니다.")

    lancedb_uri = str(os.getenv("LANCEDB_URI", "data/db/vector"))
    query_seed = _read_query_seed_from_lancedb(lancedb_uri)

    retrieved_output = await rag_retrieve_node.arun(
        {
            "user_message": query_seed,
            "rag_queries": [query_seed],
        }
    )
    retrieved_chunks = retrieved_output.get("rag_retrieved_chunks")
    assert isinstance(retrieved_chunks, list)
    assert len(retrieved_chunks) > 0

    dedup_output = rag_chunk_dedup_node.run(retrieved_output)
    candidates = dedup_output.get("rag_candidates")
    assert isinstance(candidates, list)
    assert len(candidates) > 0

    file_page_output = rag_file_page_dedup_node.run(
        {"rag_relevance_passed_docs": candidates}
    )
    final_topk_output = rag_final_topk_node.run(file_page_output)
    final_docs = final_topk_output.get("rag_filtered_docs")
    assert isinstance(final_docs, list)
    assert len(final_docs) > 0

    format_output = rag_format_node.run(
        {
            "rag_filtered_docs": final_docs,
            "rag_reference_fields": ["score", "snippet"],
            "rag_metadata_fields": [],
        }
    )
    rag_context = format_output.get("rag_context")
    rag_references = format_output.get("rag_references")
    assert isinstance(rag_context, str)
    assert rag_context.strip() != ""
    assert isinstance(rag_references, list)
    assert len(rag_references) > 0
