"""
목적: fallback 재검색 질의 생성 함수를 제공한다.
설명: 1차 관련성 결과가 없을 때 LLM으로 재검색 질의를 생성한다.
디자인 패턴: 함수형 유틸
참조: src/rag_chatbot/shared/chat/rags/schemas/keyword.py
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.rags.schemas import parse_keywords
from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk


def generate_fallback_queries(
    user_query: str,
    docs: list[RetrievedChunk],
    *,
    max_fallback_queries: int,
    prompt: str,
    llm_client: LLMClient,
    enable_llm: bool,
) -> list[str]:
    """재검색 fallback 질의를 생성한다."""

    if not enable_llm or max_fallback_queries <= 0:
        return []

    context = _build_context(docs)
    formatted_prompt = prompt.format(user_query=user_query, context=context)
    response = llm_client.invoke([HumanMessage(content=formatted_prompt)])
    raw = _extract_text(response)
    return parse_keywords(raw, max_fallback_queries)


def _build_context(docs: list[RetrievedChunk]) -> str:
    lines: list[str] = []
    for index, doc in enumerate(docs[:12]):
        lines.append(
            "[index={index}] file_name={file_name}\nbody={body}".format(
                index=index,
                file_name=doc.get("file_name", ""),
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


__all__ = ["generate_fallback_queries"]
