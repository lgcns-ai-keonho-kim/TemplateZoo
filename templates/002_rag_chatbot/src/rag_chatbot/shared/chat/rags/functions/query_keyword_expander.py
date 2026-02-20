"""
목적: 쿼리 키워드 확장 함수를 제공한다.
설명: LLM을 이용해 사용자 질의를 comma-separated 키워드로 확장한다.
디자인 패턴: 함수형 유틸
참조: src/rag_chatbot/shared/chat/rags/schemas/keyword.py
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.rags.schemas import parse_keywords
from rag_chatbot.shared.logging import Logger


def generate_query_keywords(
    user_query: str,
    *,
    max_generated_keywords: int,
    prompt: PromptTemplate | str,
    llm_client: LLMClient,
    enable_llm: bool,
    logger: Logger,
) -> list[str]:
    """유저 질의를 기반으로 검색 확장 키워드를 생성한다."""

    if not enable_llm or max_generated_keywords <= 0:
        return []

    formatted_prompt = prompt.format(user_query=user_query)
    response = llm_client.invoke([HumanMessage(content=formatted_prompt)])
    raw = _extract_text(response)
    keywords = parse_keywords(raw, max_generated_keywords)
    logger.info(
        "rag.keyword.generated: count=%s, query=%s"
        % (len(keywords), user_query[:60])
    )
    return keywords


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


__all__ = ["generate_query_keywords"]
