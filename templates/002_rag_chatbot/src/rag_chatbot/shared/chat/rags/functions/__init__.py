"""
목적: RAG 함수형 파이프라인 공개 API를 제공한다.
설명: 검색/이진 관련성 필터/포맷/전체 파이프라인 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/rag_chatbot/shared/chat/rags/functions/*.py
"""

from rag_chatbot.shared.chat.rags.functions.binary_relevance_filter import filter_by_binary_relevance
from rag_chatbot.shared.chat.rags.functions.dedup import dedup_by_file_page, merge_by_chunk_id
from rag_chatbot.shared.chat.rags.functions.format import build_rag_references, format_rag_context
from rag_chatbot.shared.chat.rags.functions.pipeline import run_rag_pipeline
from rag_chatbot.shared.chat.rags.functions.query_keyword_expander import generate_query_keywords
from rag_chatbot.shared.chat.rags.functions.retrieve import search_parallel

__all__ = [
    "run_rag_pipeline",
    "search_parallel",
    "generate_query_keywords",
    "filter_by_binary_relevance",
    "merge_by_chunk_id",
    "dedup_by_file_page",
    "format_rag_context",
    "build_rag_references",
]
