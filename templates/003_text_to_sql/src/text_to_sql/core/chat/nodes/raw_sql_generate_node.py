"""
목적: alias별 raw SQL 생성 노드를 제공한다.
설명: 선택된 각 target alias에 대해 LLM을 개별 호출해 읽기 전용 SQL 문자열을 생성한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/prompts/raw_sql_generation_prompt.py
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from text_to_sql.core.chat.prompts import RAW_SQL_GENERATION_PROMPT
from text_to_sql.integrations.llm import LLMClient
from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.exceptions import BaseAppException, ExceptionDetail
from text_to_sql.shared.logging import Logger, create_default_logger

_raw_sql_generate_logger: Logger = create_default_logger("RawSQLGenerateNode")
_raw_sql_generate_llm: LLMClient | None = None


def _require_gemini_runtime() -> tuple[str, str]:
    """Gemini 필수 런타임 설정을 검증한다."""

    model = str(os.getenv("GEMINI_MODEL", "") or "").strip()
    project = str(os.getenv("GEMINI_PROJECT", "") or "").strip()
    if not model:
        detail = ExceptionDetail(
            code="GEMINI_MODEL_MISSING",
            cause="GEMINI_MODEL 환경 변수가 비어 있습니다.",
        )
        raise BaseAppException("Gemini 모델 설정이 필요합니다.", detail)
    if not project:
        detail = ExceptionDetail(
            code="GEMINI_PROJECT_MISSING",
            cause="GEMINI_PROJECT 환경 변수가 비어 있습니다.",
        )
        raise BaseAppException("Gemini 프로젝트 설정이 필요합니다.", detail)
    return model, project


def _get_raw_sql_generate_llm() -> LLMClient:
    """raw SQL 생성용 LLMClient를 지연 초기화해 반환한다."""

    global _raw_sql_generate_llm
    if _raw_sql_generate_llm is not None:
        return _raw_sql_generate_llm
    model_name, project = _require_gemini_runtime()
    model = ChatGoogleGenerativeAI(
        model=model_name,
        project=project,
        thinking_level="minimal",
    )
    _raw_sql_generate_llm = LLMClient(
        model=model,
        name="chat-raw-sql-generate-llm",
    )
    return _raw_sql_generate_llm


def _to_input_list(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []
    result: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        result.append({str(key): value for key, value in item.items()})
    return result


def _to_retry_map(raw: object) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(alias).strip(): str(message or "").strip()
        for alias, message in raw.items()
        if str(alias).strip()
    }


def _extract_llm_text(content: object) -> str:
    """LLM 응답 content를 SQL 문자열로 정규화한다."""

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
                continue
            if isinstance(item, Mapping):
                item_map = {str(key): value for key, value in item.items()}
                text = item_map.get("text")
                if text is not None:
                    chunks.append(str(text))
                continue
            chunks.append(str(item))
        return "".join(chunks)
    if isinstance(content, Mapping):
        content_map = {str(key): value for key, value in content.items()}
        text = content_map.get("text")
        if text is not None:
            return str(text)
    return str(content)


async def _ainvoke_sql_generation(
    *,
    user_message: str,
    target_alias: str,
    target_engine: str,
    target_schema_context: str,
    sql_retry_feedback: str,
) -> str:
    """alias별 raw SQL 생성을 비동기로 수행한다."""

    prompt = RAW_SQL_GENERATION_PROMPT.format(
        user_message=user_message,
        target_alias=target_alias,
        target_engine=target_engine,
        target_schema_context=target_schema_context,
        sql_retry_feedback=sql_retry_feedback,
    )
    llm_client = _get_raw_sql_generate_llm()
    response = await llm_client.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=user_message),
        ]
    )
    text = _extract_llm_text(getattr(response, "content", "")).strip()
    if text.startswith("```"):
        stripped = text.removeprefix("```").removesuffix("```").strip()
        if stripped.lower().startswith("sql"):
            stripped = stripped[3:].strip()
        text = stripped
    return text.strip()


async def _run_raw_sql_generate_step(
    state: Mapping[str, Any],
) -> dict[str, object]:
    """alias fanout 이후 raw SQL 생성을 병렬 수행한다."""

    user_message = str(state.get("user_message") or "").strip()
    inputs = _to_input_list(state.get("raw_sql_inputs"))
    retry_feedbacks = _to_retry_map(state.get("sql_retry_feedbacks"))
    if not inputs:
        return {
            "sql_texts_by_alias": {},
            "sql_pipeline_failure_stage": "sql_generation",
            "sql_pipeline_failure_details": [
                {
                    "code": "RAW_SQL_INPUT_EMPTY",
                    "message": "SQL 생성 대상 alias 입력이 비어 있습니다.",
                }
            ],
            "sql_plan": {
                "phase": "raw_sql_generate",
                "selected_aliases": [],
                "sql_texts_by_alias": {},
            },
        }

    async def _generate_one(item: dict[str, object]) -> tuple[str, str | Exception]:
        target_alias = str(item.get("target_alias") or "").strip()
        target_engine = str(item.get("target_engine") or "").strip()
        target_schema_context = str(item.get("target_schema_context") or "").strip()
        sql_retry_feedback = retry_feedbacks.get(target_alias, "")
        try:
            sql_text = await _ainvoke_sql_generation(
                user_message=user_message,
                target_alias=target_alias,
                target_engine=target_engine,
                target_schema_context=target_schema_context,
                sql_retry_feedback=sql_retry_feedback,
            )
            return target_alias, sql_text.strip()
        except Exception as error:  # noqa: BLE001
            return target_alias, error

    results = await asyncio.gather(
        *[_generate_one(item) for item in inputs],
        return_exceptions=False,
    )

    sql_texts_by_alias: dict[str, str] = {}
    failures: list[dict[str, object]] = []
    for target_alias, result in results:
        if isinstance(result, Exception):
            failures.append(
                {
                    "target_alias": target_alias,
                    "code": "RAW_SQL_GENERATION_FAILED",
                    "message": str(result).strip() or "SQL 생성 중 오류가 발생했습니다.",
                }
            )
            continue
        if not result:
            failures.append(
                {
                    "target_alias": target_alias,
                    "code": "RAW_SQL_GENERATION_EMPTY",
                    "message": "LLM이 SQL 문자열을 반환하지 않았습니다.",
                }
            )
            continue
        sql_texts_by_alias[target_alias] = result

    failure_stage = ""
    failure_details: list[dict[str, object]] = []
    if failures:
        failure_stage = "sql_generation"
        failure_details = failures

    return {
        "sql_texts_by_alias": sql_texts_by_alias,
        "sql_pipeline_failure_stage": failure_stage,
        "sql_pipeline_failure_details": failure_details,
        "sql_plan": {
            "phase": "raw_sql_generate",
            "selected_aliases": sorted(sql_texts_by_alias.keys()),
            "sql_texts_by_alias": sql_texts_by_alias,
        },
    }

raw_sql_generate_node = function_node(
    fn=_run_raw_sql_generate_step,
    node_name="raw_sql_generate",
    logger=_raw_sql_generate_logger,
)
raw_sql_generate_retry_node = function_node(
    fn=_run_raw_sql_generate_step,
    node_name="raw_sql_generate_retry",
    logger=_raw_sql_generate_logger,
)

__all__ = ["raw_sql_generate_node", "raw_sql_generate_retry_node"]
