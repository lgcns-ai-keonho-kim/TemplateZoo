"""
목적: 메타데이터 기반 답변 컨텍스트 준비 노드를 제공한다.
설명: 직전 응답의 answer_source_meta와 사용자 질의를 기반으로 SQL 재조회 없이 답변 컨텍스트를 생성한다.
디자인 패턴: 함수 주입(Function Injection)
참조: src/text_to_sql/core/chat/nodes/context_strategy_finalize_node.py, src/text_to_sql/core/chat/nodes/response_node.py
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_metadata_answer_prepare_logger: Logger = create_default_logger(
    "MetadataAnswerPrepareNode"
)


def _to_map(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _to_string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return sorted({str(item).strip() for item in raw if str(item).strip()})


def _normalize_text(raw: object) -> str:
    return re.sub(r"\s+", " ", str(raw or "").strip().lower())


def _compact_text(raw: object) -> str:
    return re.sub(r"[\s_\-]+", "", _normalize_text(raw))


def _contains_identifier(query_text: str, query_compact: str, identifier: str) -> bool:
    candidate = str(identifier or "").strip()
    if not candidate:
        return False
    lowered = _normalize_text(candidate)
    compact = _compact_text(candidate)
    return bool(
        (lowered and lowered in query_text) or (compact and compact in query_compact)
    )


def _select_target_columns(
    *,
    user_message: str,
    column_ids: list[str],
    lineage: Mapping[str, str],
) -> list[str]:
    query_text = _normalize_text(user_message)
    query_compact = _compact_text(user_message)
    selected: list[str] = []
    for column_id in column_ids:
        source = str(lineage.get(column_id) or "").strip()
        if _contains_identifier(
            query_text, query_compact, column_id
        ) or _contains_identifier(query_text, query_compact, source):
            selected.append(column_id)
    if selected:
        return sorted({item for item in selected})
    return column_ids[:3]


def _run_metadata_answer_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """메타데이터 기반 답변 컨텍스트를 생성한다."""

    user_message = str(state.get("user_message") or "").strip()
    answer_source_meta = _to_map(state.get("answer_source_meta"))
    table_ids = _to_string_list(answer_source_meta.get("table_ids"))
    column_ids = _to_string_list(answer_source_meta.get("column_ids"))
    column_descriptions = _to_map(answer_source_meta.get("column_descriptions"))
    lineage = {
        str(key): str(value)
        for key, value in _to_map(answer_source_meta.get("lineage")).items()
        if str(key).strip() and str(value).strip()
    }

    selected_columns = _select_target_columns(
        user_message=user_message,
        column_ids=column_ids,
        lineage=lineage,
    )

    context_lines: list[str] = []
    context_lines.append(f"- 사용자 질문: {user_message}")
    context_lines.append(
        f"- 참조 테이블: {', '.join(table_ids) if table_ids else '(없음)'}"
    )

    description_lines: list[str] = []
    for column_id in selected_columns:
        if not column_id:
            continue
        source_column = lineage.get(column_id, column_id)
        description = str(column_descriptions.get(column_id) or "").strip()
        if not description and source_column != column_id:
            description = str(column_descriptions.get(source_column) or "").strip()
        if not description:
            continue
        if source_column != column_id:
            description_lines.append(f"- {column_id}({source_column}): {description}")
        else:
            description_lines.append(f"- {column_id}: {description}")
        if len(description_lines) >= 8:
            break

    if description_lines:
        context_lines.append("- 컬럼 의미:")
        context_lines.extend(description_lines)
        metadata_route = "response"
        sql_pipeline_failure_stage = ""
        sql_pipeline_failure_details: list[dict[str, str]] = []
    else:
        metadata_route = "sql"
        sql_pipeline_failure_stage = ""
        sql_pipeline_failure_details = []
        sql_answer_context = ""
        _metadata_answer_prepare_logger.debug(
            "metadata.answer.prepare: metadata 부족으로 SQL 재실행 경로로 전환"
        )
        return {
            "sql_answer_context": sql_answer_context,
            "metadata_route": metadata_route,
            "sql_pipeline_failure_stage": sql_pipeline_failure_stage,
            "sql_pipeline_failure_details": sql_pipeline_failure_details,
        }

    sql_answer_context = "\n".join(context_lines)
    _metadata_answer_prepare_logger.debug(
        "metadata.answer.prepare: tables=%s, selected_columns=%s, described_columns=%s"
        % (len(table_ids), len(selected_columns), len(description_lines))
    )
    return {
        "sql_answer_context": sql_answer_context,
        "metadata_route": metadata_route,
        "sql_pipeline_failure_stage": sql_pipeline_failure_stage,
        "sql_pipeline_failure_details": sql_pipeline_failure_details,
    }


metadata_answer_prepare_node = function_node(
    fn=_run_metadata_answer_prepare_step,
    node_name="metadata_answer_prepare",
    logger=_metadata_answer_prepare_logger,
)

__all__ = ["metadata_answer_prepare_node"]
