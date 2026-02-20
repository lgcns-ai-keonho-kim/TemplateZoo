"""
목적: 표 주석(요약/설명) 생성 유틸을 제공한다.
설명: 추출된 HTML 표와 페이지 텍스트를 입력받아 [TBL] 태그 포맷 본문을 생성한다.
디자인 패턴: 함수형 유틸 모듈
참조: ingestion/core/file_parser.py, ingestion/core/pdf_tables.py
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Sequence

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_TABLE_ANALYSIS_PATTERN = re.compile(
    r"<SUMMARY>(?P<summary>.*?)</SUMMARY>\s*<DESCRIPTION>(?P<description>.*?)</DESCRIPTION>",
    flags=re.DOTALL,
)
_MAX_PROMPT_TABLE_CHARS = 40_000
_MAX_PAGE_TEXT_CHARS = 6_000

_TABLE_PROMPT_TEMPLATE = """
아래 표 HTML과 페이지 텍스트를 바탕으로 표 내용을 분석하라.

[출력 형식 - 반드시 그대로]
<SUMMARY>최대 5문장 요약</SUMMARY>
<DESCRIPTION>최대 3문단 상세 설명</DESCRIPTION>

[강제 규칙]
1) 위 태그 외 어떤 텍스트도 출력하지 마라.
2) SUMMARY는 최대 5문장으로 작성하라.
3) DESCRIPTION은 최대 3문단으로 작성하라.
4) 표에 없는 내용을 추측해서 쓰지 마라.
5) 한국어로 작성하라.

[표 HTML]
{table_html}

[페이지 텍스트]
{page_text}
""".strip()


@dataclass(frozen=True)
class TableAnnotationTask:
    """표 주석 생성 입력 모델."""

    task_id: str
    page_num: int
    table_html: str
    page_text: str


def annotate_table_tasks(
    tasks: Sequence[TableAnnotationTask],
    *,
    workers: int | None = None,
) -> dict[str, str]:
    """표 주석 태스크를 병렬 처리해 task_id별 [TBL] 본문을 반환한다."""

    if not tasks:
        return {}

    worker_count = _resolve_worker_count(task_count=len(tasks), workers=workers)
    print(
        f"[진행][table-llm] 주석 생성 시작: 작업 {len(tasks)}개, 워커 {worker_count}개"
    )
    resolved = asyncio.run(_annotate_table_tasks_async(tasks=tasks, workers=worker_count))
    print("[진행][table-llm] 주석 생성 완료")
    return resolved


async def _annotate_table_tasks_async(
    *,
    tasks: Sequence[TableAnnotationTask],
    workers: int,
) -> dict[str, str]:
    """표 주석 태스크를 비동기로 병렬 처리한다."""

    semaphore = asyncio.Semaphore(max(1, workers))
    coroutines = [
        _annotate_single_task(task=task, semaphore=semaphore)
        for task in tasks
    ]
    gathered = await asyncio.gather(*coroutines)

    resolved: dict[str, str] = {}
    for index, (task_id, body) in enumerate(gathered, start=1):
        resolved[task_id] = body
        print(f"[진행][table-llm] 처리 {index}/{len(tasks)}")
    return resolved


async def _annotate_single_task(
    *,
    task: TableAnnotationTask,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str]:
    """단일 표의 [TBL] 본문을 생성한다."""

    table_html_full = _normalize_full_table_html(task.table_html)
    table_html_for_prompt = _normalize_prompt_table_html(table_html_full)
    page_text = _normalize_page_text(task.page_text)
    prompt = _TABLE_PROMPT_TEMPLATE.format(
        table_html=table_html_for_prompt,
        page_text=page_text,
    )

    try:
        async with semaphore:
            model = _create_llm_model()
            response = await model.ainvoke([HumanMessage(content=prompt)])
    except Exception as error:
        detail = ExceptionDetail(
            code="INGESTION_TABLE_ANNOTATION_FAILED",
            cause=(
                "표 주석 생성 실패: "
                f"task_id={task.task_id}, page={int(task.page_num)}, error={error!s}"
            ),
        )
        # 멀티프로세스 직렬화 안정성을 위해 원본 예외 객체를 직접 보관하지 않는다.
        raise BaseAppException("표 주석 생성에 실패했습니다.", detail) from None
    raw = _extract_message_text(response).strip()
    summary, description = _extract_summary_description(raw)
    body = (
        "[TBL]\n"
        f"<HTML>{table_html_full}</HTML>\n"
        f"<SUMMARY>{summary}</SUMMARY>\n"
        f"<DESCRIPTION>{description}</DESCRIPTION>\n"
        "[/TBL]"
    )
    return task.task_id, body


def _create_llm_model() -> ChatOpenAI:
    """표 주석용 모델을 생성한다."""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        detail = ExceptionDetail(
            code="INGESTION_OPENAI_API_KEY_MISSING",
            cause="OPENAI_API_KEY 환경 변수가 비어 있습니다.",
        )
        raise BaseAppException("표 주석 생성을 위해 OPENAI_API_KEY가 필요합니다.", detail)

    model_name = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        temperature=0.0,
    )


def _normalize_full_table_html(table_html: str) -> str:
    """저장용 전체 HTML을 정규화한다."""

    normalized = str(table_html or "").strip()
    if not normalized:
        return "<table><tbody><tr><td></td></tr></tbody></table>"
    return normalized


def _normalize_prompt_table_html(table_html: str) -> str:
    """LLM 프롬프트 입력용 HTML 길이를 제한한다."""

    normalized = str(table_html or "").strip()
    if len(normalized) <= _MAX_PROMPT_TABLE_CHARS:
        return normalized
    return normalized[:_MAX_PROMPT_TABLE_CHARS]


def _normalize_page_text(text: str) -> str:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return "페이지 텍스트 없음"
    if len(normalized) <= _MAX_PAGE_TEXT_CHARS:
        return normalized
    return normalized[:_MAX_PAGE_TEXT_CHARS]


def _extract_message_text(message: object) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts: list[str] = []
        for item in content:
            if isinstance(item, str):
                texts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if text is not None:
                    texts.append(str(text))
        return "".join(texts)
    if isinstance(content, dict):
        text = content.get("text")
        return "" if text is None else str(text)
    return str(content)


def _extract_summary_description(raw: str) -> tuple[str, str]:
    matched = _TABLE_ANALYSIS_PATTERN.search(raw)
    if matched is None:
        detail = ExceptionDetail(
            code="INGESTION_TABLE_ANNOTATION_FORMAT_INVALID",
            cause=f"raw={raw[:240]}",
        )
        raise BaseAppException("표 주석 출력 형식이 올바르지 않습니다.", detail)
    summary = _sanitize_text(matched.group("summary"))
    description = _sanitize_text(matched.group("description"))
    return summary, description


def _sanitize_text(text: str) -> str:
    normalized = " ".join(str(text or "").split())
    normalized = normalized.replace("<", " ").replace(">", " ")
    return normalized.strip()


def _resolve_worker_count(*, task_count: int, workers: int | None) -> int:
    if task_count <= 1:
        return 1
    if workers is None or workers <= 0:
        cpu_count = os.cpu_count() or 1
        return max(1, min(cpu_count, task_count, 8))
    return max(1, min(int(workers), task_count))


__all__ = ["TableAnnotationTask", "annotate_table_tasks"]
