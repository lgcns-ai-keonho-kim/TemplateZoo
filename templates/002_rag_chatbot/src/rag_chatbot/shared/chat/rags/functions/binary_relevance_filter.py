"""
목적: 이진(0/1) 관련성 필터 함수를 제공한다.
설명: 각 검색 청크를 LLM 비동기 판정(ainvoke)으로 통과/탈락 처리한다.
디자인 패턴: 함수형 유틸
참조: src/rag_chatbot/shared/chat/rags/schemas/binary.py
"""

from __future__ import annotations

import asyncio
import threading

from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.chat.rags.schemas import parse_binary_relevance
from rag_chatbot.shared.chat.rags.types.retrieval import RetrievedChunk
from rag_chatbot.shared.logging import Logger

_DEFAULT_CONCURRENCY = 8


def filter_by_binary_relevance(
    docs: list[RetrievedChunk],
    user_query: str,
    *,
    prompt: PromptTemplate | str,
    llm_client: LLMClient,
    enable_llm: bool,
    logger: Logger,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> list[RetrievedChunk]:
    """청크별 0/1 판정으로 관련 문서만 반환한다."""

    if not docs:
        return []
    if not enable_llm:
        return docs

    filtered = _run_async(
        _filter_by_binary_relevance_async(
            docs=docs,
            user_query=user_query,
            prompt=prompt,
            llm_client=llm_client,
            logger=logger,
            concurrency=concurrency,
        )
    )
    logger.info(
        "rag.binary.filtered: input=%s, passed=%s"
        % (len(docs), len(filtered))
    )
    return filtered


async def _filter_by_binary_relevance_async(
    *,
    docs: list[RetrievedChunk],
    user_query: str,
    prompt: str,
    llm_client: LLMClient,
    logger: Logger,
    concurrency: int,
) -> list[RetrievedChunk]:
    """청크별 비동기 판정 태스크를 병렬 실행한다."""

    semaphore = asyncio.Semaphore(max(1, int(concurrency)))
    tasks = [
        _judge_single_chunk(
            doc=doc,
            user_query=user_query,
            prompt=prompt,
            llm_client=llm_client,
            logger=logger,
            semaphore=semaphore,
        )
        for doc in docs
    ]
    flags = await asyncio.gather(*tasks)
    return [
        doc
        for doc, passed in zip(docs, flags, strict=True)
        if passed
    ]


async def _judge_single_chunk(
    *,
    doc: RetrievedChunk,
    user_query: str,
    prompt: PromptTemplate | str,
    llm_client: LLMClient,
    logger: Logger,
    semaphore: asyncio.Semaphore,
) -> bool:
    """단일 청크의 이진 관련성 여부를 판정한다."""

    formatted_prompt = prompt.format(
        user_query=user_query,
        body=doc.get("body", ""),
    )

    try:
        async with semaphore:
            response = await llm_client.ainvoke([HumanMessage(content=formatted_prompt)])
        raw = _extract_text(response)
        return parse_binary_relevance(raw) == 1
    except Exception as error:  # noqa: BLE001 - 개별 청크 실패 격리
        logger.warning(
            "rag.binary.filter.error: file=%s, error=%s"
            % (doc.get("file_name", ""), error)
        )
        return False


def _run_async(coro):
    """동기 컨텍스트에서 비동기 코루틴을 안전하게 실행한다."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result_holder: dict[str, object] = {}
    error_holder: dict[str, BaseException] = {}

    def runner() -> None:
        try:
            result_holder["value"] = asyncio.run(coro)
        except BaseException as error:  # pragma: no cover - 비동기 분기 안전망
            error_holder["error"] = error

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in error_holder:
        raise error_holder["error"]
    return result_holder.get("value", [])


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


__all__ = ["filter_by_binary_relevance"]
