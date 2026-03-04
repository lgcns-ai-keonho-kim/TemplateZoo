"""
목적: 표 주석(요약/설명) 생성 유틸을 제공한다.
설명: 추출된 HTML 표와 페이지 컨텍스트(텍스트/이미지)를 입력받아 [TBL] 태그 포맷 본문을 생성한다.
디자인 패턴: 함수형 유틸 모듈
참조: ingestion/core/file_parser.py, ingestion/core/pdf_tables.py
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, cast

from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_TABLE_ANALYSIS_PATTERN = re.compile(
    r"<SUMMARY>(?P<summary>.*?)</SUMMARY>\s*<DESCRIPTION>(?P<description>.*?)</DESCRIPTION>",
    flags=re.DOTALL,
)
_MAX_PROMPT_TABLE_CHARS = 40_000
_MAX_PAGE_TEXT_CHARS = 6_000

_TABLE_TEXT_PROMPT_TEMPLATE = """
<system>
You are a table analysis specialist. Your sole task is to generate structured annotations for HTML tables based on the provided table markup and surrounding page text.
</system>

<instructions>
Analyze the provided HTML table and generate a structured annotation using ONLY the information explicitly present in the table and the surrounding page text. Do not infer, assume, or hallucinate any content beyond what is directly stated.

Your response MUST adhere to the following rules without exception:
  1. Output ONLY the annotation block below — no preamble, explanation, commentary, or trailing text of any kind.
  2. SUMMARY must be written in 5 sentences or fewer.
  3. DESCRIPTION must be written in 3 paragraphs or fewer.
  4. Base all content strictly on the table content and the provided page text. Do not speculate or fill in gaps.
  5. Write all content in Korean.
</instructions>

<output_format>
Reproduce this structure exactly:

[TBL]
<TBL>HTML table</TBL>
<SUMMARY>5문장 이내 요약</SUMMARY>
<DESCRIPTION>3문단 이내 상세 설명</DESCRIPTION>
[/TBL]
</output_format>

<input>
  <table_html>{table_html}</table_html>
  <page_text>{page_text}</page_text>
</input>
""".strip()

_TABLE_IMAGE_PROMPT_TEMPLATE = """
<system>
You are a table analysis specialist. Your sole task is to generate structured annotations for HTML tables based on the provided page image and surrounding page text.
</system>

<instructions>
Analyze the table using the page image as the primary source. The table HTML is provided as a structural reference.
Generate a structured annotation using ONLY information that is visible in the page image or explicitly present in the page text.
Do not infer, assume, or hallucinate content.

Your response MUST adhere to the following rules without exception:
  1. Output ONLY the annotation block below — no preamble, explanation, commentary, or trailing text.
  2. SUMMARY must be written in 5 sentences or fewer.
  3. DESCRIPTION must be written in 3 paragraphs or fewer.
  4. Write all content in Korean.
</instructions>

<output_format>
Reproduce this structure exactly:

[TBL]
<TBL>HTML table</TBL>
<SUMMARY>5문장 이내 요약</SUMMARY>
<DESCRIPTION>3문단 이내 상세 설명</DESCRIPTION>
[/TBL]
</output_format>

<input>
  <page_image_path>{page_image_path}</page_image_path>
  <table_html>{table_html}</table_html>
  <page_text>{page_text}</page_text>
</input>
""".strip()


@dataclass(frozen=True)
class TableAnnotationTask:
    """표 주석 생성 입력 모델."""

    task_id: str
    page_num: int
    table_html: str
    page_text: str
    page_image_path: Path | None = None


def annotate_table_tasks(
    tasks: Sequence[TableAnnotationTask],
    *,
    model: BaseChatModel,
    workers: int | None = None,
) -> dict[str, str]:
    """표 주석 태스크를 병렬 처리해 task_id별 [TBL] 본문을 반환한다."""

    if not tasks:
        return {}

    worker_count = _resolve_worker_count(task_count=len(tasks), workers=workers)
    print(
        f"[진행][table-llm] 주석 생성 시작: 작업 {len(tasks)}개, 워커 {worker_count}개"
    )
    resolved = asyncio.run(
        _annotate_table_tasks_async(
            tasks=tasks,
            workers=worker_count,
            model=model,
        )
    )
    print("[진행][table-llm] 주석 생성 완료")
    return resolved


async def _annotate_table_tasks_async(
    *,
    tasks: Sequence[TableAnnotationTask],
    workers: int,
    model: BaseChatModel,
) -> dict[str, str]:
    """표 주석 태스크를 비동기로 병렬 처리한다."""

    semaphore = asyncio.Semaphore(max(1, workers))
    coroutines = [
        _annotate_single_task(task=task, semaphore=semaphore, model=model)
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
    model: BaseChatModel,
) -> tuple[str, str]:
    """단일 표의 [TBL] 본문을 생성한다."""

    table_html_full = _normalize_full_table_html(task.table_html)
    table_html_for_prompt = _normalize_prompt_table_html(table_html_full)
    page_text = _normalize_page_text(task.page_text)

    try:
        async with semaphore:
            response = await _invoke_table_model(
                model=model,
                task=task,
                table_html_for_prompt=table_html_for_prompt,
                page_text=page_text,
            )
    except BaseAppException:
        raise
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
        f"<TBL>{table_html_full}</TBL>\n"
        f"<SUMMARY>{summary}</SUMMARY>\n"
        f"<DESCRIPTION>{description}</DESCRIPTION>\n"
        "[/TBL]"
    )
    return task.task_id, body


async def _invoke_table_model(
    *,
    model: BaseChatModel,
    task: TableAnnotationTask,
    table_html_for_prompt: str,
    page_text: str,
) -> object:
    """표 주석 모델 호출을 수행한다."""

    if task.page_image_path is None:
        prompt = _TABLE_TEXT_PROMPT_TEMPLATE.format(
            table_html=table_html_for_prompt,
            page_text=page_text,
        )
        return await model.ainvoke([HumanMessage(content=prompt)])

    page_image_path = Path(task.page_image_path)
    if not page_image_path.exists():
        detail = ExceptionDetail(
            code="INGESTION_TABLE_PAGE_IMAGE_NOT_FOUND",
            cause=f"task_id={task.task_id}, path={page_image_path.as_posix()}",
        )
        raise BaseAppException("표 주석용 페이지 이미지를 찾을 수 없습니다.", detail)

    prompt = _TABLE_IMAGE_PROMPT_TEMPLATE.format(
        page_image_path=page_image_path.as_posix(),
        table_html=table_html_for_prompt,
        page_text=page_text,
    )
    image_data_url = _to_data_url(page_image_path)
    return await model.ainvoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ]
            )
        ]
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


def _to_data_url(image_path: Path) -> str:
    """이미지 파일을 data URL 문자열로 변환한다."""

    raw = image_path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    suffix = image_path.suffix.lower()
    if suffix == ".jpg":
        suffix = ".jpeg"
    mime = {
        ".png": "image/png",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "image/png")
    return f"data:{mime};base64,{encoded}"


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
                item_dict = cast(dict[str, object], item)
                text = item_dict.get("text")
                if text is not None:
                    texts.append(str(text))
        return "".join(texts)
    if isinstance(content, dict):
        content_dict = cast(dict[str, object], content)
        text = content_dict.get("text")
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
