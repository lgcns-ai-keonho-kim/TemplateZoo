"""
목적: 관련성 필터 함수를 제공한다.
설명: LLM이 반환한 index 집합 기준으로 검색 후보를 필터링한다.
디자인 패턴: 함수형 유틸
참조: src/rag_chatbot/shared/chat/rags/schemas/relevance.py
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.rags.schemas import parse_relevance_indexes
from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk
from rag_chatbot.shared.logging import Logger


def filter_by_relevance(
    docs: list[RetrievedChunk],
    user_query: str,
    *,
    top_k: int,
    prompt: str,
    llm_client: LLMClient,
    enable_llm: bool,
    stage: str,
    lane: str,
    logger: Logger,
) -> list[RetrievedChunk]:
    """관련성 필터를 수행해 문서 목록을 반환한다."""

    if not docs:
        return []
    candidates = docs[: max(1, top_k)]
    if not enable_llm:
        return candidates

    context = _build_context(candidates)
    formatted_prompt = prompt.format(user_query=user_query, context=context)
    response = llm_client.invoke([HumanMessage(content=formatted_prompt)])
    raw = _extract_text(response)
    selected_indexes = parse_relevance_indexes(raw, len(candidates))

    logger.info(
        "rag.relevance.filtered: stage=%s, lane=%s, input=%s, selected=%s"
        % (stage, lane, len(candidates), len(selected_indexes))
    )

    if not selected_indexes:
        return []
    return [candidates[index] for index in selected_indexes]


def _build_context(docs: list[RetrievedChunk]) -> str:
    lines: list[str] = []
    for index, doc in enumerate(docs):
        metadata = doc.get("metadata") or {}
        page_num = metadata.get("page_num") if isinstance(metadata, dict) else None
        lines.append(
            "[index={index}] file_name={file_name} page={page} score={score:.6f}\nbody={body}".format(
                index=index,
                file_name=doc.get("file_name", ""),
                page=page_num,
                score=float(doc.get("score", 0.0)),
                body=doc.get("body", ""),
            )
        )
    return "\n\n".join(lines)


def _extract_text(message: object) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if text is not None:
                    chunks.append(str(text))
        return "".join(chunks)
    if isinstance(content, dict):
        text = content.get("text")
        if text is None:
            return ""
        return str(text)
    return str(content)


__all__ = ["filter_by_relevance"]
