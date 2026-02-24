"""
목적: 이미지 주석(요약/설명) 생성 유틸을 제공한다.
설명: 멀티모달 LLM으로 이미지와 페이지 텍스트를 입력받아 [IMG] 태그 포맷 본문을 생성한다.
디자인 패턴: 함수형 유틸 모듈
참조: ingestion/core/file_parser.py, ingestion/core/pdf_assets.py
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail

_IMG_BLOCK_PATTERN = re.compile(
    r"\[IMG\]\s*<PATH>(?P<path>.*?)</PATH>\s*<SUMMARY>(?P<summary>.*?)</SUMMARY>\s*"
    r"<DESCRIPTION>(?P<description>.*?)</DESCRIPTION>\s*\[/IMG\]",
    flags=re.DOTALL,
)
_MAX_PAGE_TEXT_CHARS = 6000

_ANNOTATION_PROMPT_TEMPLATE = """
<system>
You are an image annotation specialist. Your sole task is to generate structured annotations for images based on the provided image path and surrounding page text.
</system>

<instructions>
Generate a structured image annotation using ONLY the information explicitly present in the image and the provided page text. Do not infer, assume, or hallucinate any content beyond what is directly observable or stated.

Your response MUST adhere to the following rules without exception:
  1. Output ONLY the annotation block below — no preamble, explanation, commentary, or trailing text of any kind.
  2. Preserve the PATH value exactly as given in the input; do not modify it in any way.
  3. SUMMARY must be written in 5 sentences or fewer.
  4. DESCRIPTION must be written in 3 paragraphs or fewer.
  5. Base all content strictly on the image content and the provided page text. Do not speculate.
  6. Write all content in Korean.
</instructions>

<output_format>
Reproduce this structure exactly:

[IMG]
<PATH>{image_path}</PATH>
<SUMMARY>5문장 이내 요약</SUMMARY>
<DESCRIPTION>3문단 이내 상세 설명</DESCRIPTION>
[/IMG]
</output_format>

<input>
  <image_path>{image_path}</image_path>
  <page_text>{page_text}</page_text>
</input>
""".strip()


@dataclass(frozen=True)
class ImageAnnotationTask:
    """이미지 주석 생성 입력 모델."""

    page_num: int
    image_path: Path
    page_text: str


def annotate_image_tasks(
    tasks: Sequence[ImageAnnotationTask],
    *,
    workers: int | None = None,
) -> list[tuple[str, dict[str, object]]]:
    """이미지 주석 태스크를 병렬 처리해 ingestion row 목록으로 변환한다."""

    if not tasks:
        return []

    worker_count = _resolve_worker_count(task_count=len(tasks), workers=workers)
    print(
        f"[진행][image-llm] 주석 생성 시작: 작업 {len(tasks)}개, 워커 {worker_count}개"
    )
    rows = asyncio.run(_annotate_image_tasks_async(tasks=tasks, workers=worker_count))
    print("[진행][image-llm] 주석 생성 완료")
    return rows


async def _annotate_image_tasks_async(
    *,
    tasks: Sequence[ImageAnnotationTask],
    workers: int,
) -> list[tuple[str, dict[str, object]]]:
    """이미지 주석 태스크를 비동기로 병렬 처리한다."""

    semaphore = asyncio.Semaphore(max(1, workers))
    coroutines = [
        _annotate_single_task(task=task, semaphore=semaphore)
        for task in tasks
    ]
    gathered = await asyncio.gather(*coroutines)

    rows: list[tuple[str, dict[str, object]]] = []
    for index, row in enumerate(gathered, start=1):
        rows.append(row)
        print(f"[진행][image-llm] 처리 {index}/{len(tasks)}")
    return rows


async def _annotate_single_task(
    *,
    task: ImageAnnotationTask,
    semaphore: asyncio.Semaphore,
) -> tuple[str, dict[str, object]]:
    """단일 이미지에 대한 주석 본문과 메타데이터를 생성한다."""

    image_path = Path(task.image_path)
    if not image_path.exists():
        detail = ExceptionDetail(
            code="INGESTION_IMAGE_NOT_FOUND",
            cause=f"path={image_path}",
        )
        raise BaseAppException("이미지 파일을 찾을 수 없습니다.", detail)

    image_data_url = _to_data_url(image_path)
    page_text = _normalize_page_text(task.page_text)
    prompt = _ANNOTATION_PROMPT_TEMPLATE.format(
        image_path=image_path.as_posix(),
        page_text=page_text,
    )

    try:
        async with semaphore:
            model = _create_vision_model()
            response = await model.ainvoke(
                [
                    HumanMessage(
                        content=[
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_data_url}},
                        ]
                    )
                ]
            )
    except Exception as error:
        detail = ExceptionDetail(
            code="INGESTION_IMAGE_ANNOTATION_FAILED",
            cause=(
                "이미지 주석 생성 실패: "
                f"page={int(task.page_num)}, path={image_path.as_posix()}, error={error!s}"
            ),
        )
        # 멀티프로세스 직렬화 안정성을 위해 원본 예외 객체를 직접 보관하지 않는다.
        raise BaseAppException("이미지 주석 생성에 실패했습니다.", detail) from None
    raw = _extract_message_text(response).strip()
    body = _normalize_img_block(raw, image_path=image_path)
    metadata: dict[str, object] = {
        "page_num": int(task.page_num),
        "block_type": "image",
        "layout_type": "image_annotation",
    }
    return body, metadata


def _create_vision_model() -> ChatOpenAI:
    """이미지 주석용 멀티모달 모델 인스턴스를 생성한다."""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        detail = ExceptionDetail(
            code="INGESTION_OPENAI_API_KEY_MISSING",
            cause="OPENAI_API_KEY 환경 변수가 비어 있습니다.",
        )
        raise BaseAppException("이미지 주석 생성을 위해 OPENAI_API_KEY가 필요합니다.", detail)

    model_name = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        temperature=0.0,
    )


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


def _normalize_page_text(text: str) -> str:
    """프롬프트 입력용 페이지 텍스트를 길이 제한 내로 정규화한다."""

    normalized = " ".join(str(text or "").split())
    if not normalized:
        return "페이지 텍스트 없음"
    if len(normalized) <= _MAX_PAGE_TEXT_CHARS:
        return normalized
    return normalized[:_MAX_PAGE_TEXT_CHARS]


def _extract_message_text(message: object) -> str:
    """LangChain 메시지 객체에서 텍스트를 추출한다."""

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


def _normalize_img_block(raw: str, *, image_path: Path) -> str:
    """LLM 출력에서 [IMG] 블록을 추출하고 강제 정규화한다."""

    matched = _IMG_BLOCK_PATTERN.search(raw)
    if matched is None:
        detail = ExceptionDetail(
            code="INGESTION_IMAGE_ANNOTATION_FORMAT_INVALID",
            cause=f"raw={raw[:240]}",
        )
        raise BaseAppException("이미지 주석 출력 형식이 올바르지 않습니다.", detail)

    summary = _sanitize_text(matched.group("summary"))
    description = _sanitize_text(matched.group("description"))
    normalized_path = image_path.as_posix()
    return (
        "[IMG]\n"
        f"<PATH>{normalized_path}</PATH>\n"
        f"<SUMMARY>{summary}</SUMMARY>\n"
        f"<DESCRIPTION>{description}</DESCRIPTION>\n"
        "[/IMG]"
    )


def _sanitize_text(text: str) -> str:
    """태그 본문용 텍스트를 정제한다."""

    normalized = " ".join(str(text or "").split())
    normalized = normalized.replace("<", " ").replace(">", " ")
    return normalized.strip()


def _resolve_worker_count(*, task_count: int, workers: int | None) -> int:
    """이미지 주석 워커 수를 계산한다."""

    if task_count <= 1:
        return 1

    if workers is None or workers <= 0:
        cpu_count = os.cpu_count() or 1
        return max(1, min(cpu_count, task_count, 8))

    return max(1, min(int(workers), task_count))


__all__ = ["ImageAnnotationTask", "annotate_image_tasks"]
