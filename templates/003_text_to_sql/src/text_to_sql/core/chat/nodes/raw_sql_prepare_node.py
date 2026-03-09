"""
목적: alias별 raw SQL 생성 입력을 준비한다.
설명: 선택된 target alias별 스키마 컨텍스트와 엔진 정보를 정규화해 SQL 생성 노드에 전달한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/nodes/raw_sql_generate_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.integrations.db import QueryTargetRegistry
from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.chat.runtime import get_query_target_registry
from text_to_sql.shared.logging import Logger, create_default_logger

_raw_sql_prepare_logger: Logger = create_default_logger("RawSQLPrepareNode")


def _to_schema_snapshot(raw: object) -> dict[str, dict[str, object]]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, dict[str, object]] = {}
    for table_id, raw_spec in raw.items():
        normalized_table_id = str(table_id or "").strip()
        if not normalized_table_id or not isinstance(raw_spec, Mapping):
            continue
        result[normalized_table_id] = {
            str(key): value for key, value in raw_spec.items()
        }
    return result


def _resolve_registry(raw: object) -> QueryTargetRegistry | None:
    if isinstance(raw, QueryTargetRegistry):
        return raw
    return get_query_target_registry()


def _selected_aliases(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item or "").strip() for item in raw if str(item or "").strip()]


def _build_target_schema_context(
    *,
    alias: str,
    schema_snapshot: Mapping[str, dict[str, object]],
) -> str:
    lines: list[str] = []
    for table_id, spec in sorted(schema_snapshot.items()):
        if str(spec.get("target_alias") or "").strip() != alias:
            continue
        qualified_table_name = str(
            spec.get("qualified_table_name") or spec.get("table_name") or ""
        ).strip()
        description = str(spec.get("description") or "").strip()
        primary_keys = spec.get("primary_keys")
        foreign_keys = spec.get("foreign_keys")
        lines.append(f"table_id={table_id}")
        lines.append(f"qualified_table_name={qualified_table_name}")
        if description:
            lines.append(f"table_description={description}")
        if isinstance(primary_keys, list) and primary_keys:
            lines.append(
                "primary_keys="
                + ", ".join(
                    str(item or "").strip()
                    for item in primary_keys
                    if str(item or "").strip()
                )
            )
        if isinstance(foreign_keys, list) and foreign_keys:
            fk_entries: list[str] = []
            for fk in foreign_keys:
                if not isinstance(fk, Mapping):
                    continue
                normalized_fk = {str(key): value for key, value in fk.items()}
                column = str(normalized_fk.get("column") or "").strip()
                ref_table = str(normalized_fk.get("ref_table") or "").strip()
                ref_column = str(normalized_fk.get("ref_column") or "").strip()
                if column and ref_table and ref_column:
                    fk_entries.append(f"{column}->{ref_table}.{ref_column}")
            if fk_entries:
                lines.append("foreign_keys=" + ", ".join(fk_entries))
        columns = spec.get("columns")
        if isinstance(columns, list) and columns:
            lines.append("columns=")
            column_types = spec.get("column_types")
            column_descriptions = spec.get("column_descriptions")
            quoted_table_name = str(spec.get("quoted_qualified_table_name") or "").strip()
            normalized_column_types = (
                {str(key): value for key, value in column_types.items()}
                if isinstance(column_types, Mapping)
                else {}
            )
            normalized_column_descriptions = (
                {str(key): value for key, value in column_descriptions.items()}
                if isinstance(column_descriptions, Mapping)
                else {}
            )
            raw_quoted_columns = spec.get("quoted_columns")
            quoted_columns = (
                {str(key): value for key, value in raw_quoted_columns.items()}
                if isinstance(raw_quoted_columns, Mapping)
                else {}
            )
            if quoted_table_name:
                lines.append(f"quoted_table_name={quoted_table_name}")
            for column in columns:
                column_name = str(column or "").strip()
                if not column_name:
                    continue
                column_type = str(
                    normalized_column_types.get(column_name) or ""
                ).strip()
                column_description = str(
                    normalized_column_descriptions.get(column_name) or ""
                ).strip()
                quoted_column = str(quoted_columns.get(column_name) or "").strip()
                lines.append(
                    "  - "
                    f"{column_name} | quoted={quoted_column or column_name} | "
                    f"type={column_type or 'unknown'} | description={column_description}"
                )
        lines.append("")
    return "\n".join(lines).strip()


def _run_raw_sql_prepare_step(state: Mapping[str, Any]) -> dict[str, object]:
    """alias별 raw SQL 생성 입력을 만든다."""

    schema_snapshot = _to_schema_snapshot(state.get("schema_snapshot"))
    query_target_registry = _resolve_registry(state.get("query_target_registry"))
    selected_aliases = _selected_aliases(state.get("selected_target_aliases"))
    inputs: list[dict[str, object]] = []
    for alias in selected_aliases:
        target = (
            query_target_registry.get(alias)
            if query_target_registry is not None
            else None
        )
        engine = str(target.engine or "").strip().lower() if target is not None else ""
        inputs.append(
            {
                "target_alias": alias,
                "target_engine": engine,
                "target_schema_context": _build_target_schema_context(
                    alias=alias,
                    schema_snapshot=schema_snapshot,
                ),
            }
        )

    if not inputs:
        return {
            "raw_sql_inputs": [],
            "sql_pipeline_failure_stage": "schema_selection",
            "sql_pipeline_failure_details": [
                {
                    "code": "TARGET_ALIAS_SELECTION_EMPTY",
                    "message": "실행 가능한 SQL target alias가 없습니다.",
                }
            ],
        }

    return {
        "raw_sql_inputs": inputs,
        "sql_texts_by_alias": {},
        "sql_retry_feedbacks": {},
        "execution_reports": {},
        "retry_count_by_alias": {},
        "sql_pipeline_failure_stage": "",
        "sql_pipeline_failure_details": [],
    }


raw_sql_prepare_node = function_node(
    fn=_run_raw_sql_prepare_step,
    node_name="raw_sql_prepare",
    logger=_raw_sql_prepare_logger,
)

__all__ = ["raw_sql_prepare_node"]
