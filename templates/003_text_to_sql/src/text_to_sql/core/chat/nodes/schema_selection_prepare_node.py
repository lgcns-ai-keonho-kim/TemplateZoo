"""
목적: 스키마 선택 LLM 입력 컨텍스트를 준비한다.
설명: SQL 지원 alias별 테이블/컬럼/설명을 문자열 컨텍스트로 정규화해 selection 프롬프트에 전달한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/nodes/schema_selection_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.integrations.db import QueryTargetRegistry
from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.chat.runtime import get_query_target_registry
from text_to_sql.shared.logging import Logger, create_default_logger

_schema_selection_prepare_logger: Logger = create_default_logger(
    "SchemaSelectionPrepareNode"
)


def _to_schema_snapshot(raw: object) -> dict[str, dict[str, object]]:
    if not isinstance(raw, Mapping):
        return {}
    snapshot: dict[str, dict[str, object]] = {}
    for table_id, raw_spec in raw.items():
        normalized_table_id = str(table_id or "").strip()
        if not normalized_table_id or not isinstance(raw_spec, Mapping):
            continue
        snapshot[normalized_table_id] = {
            str(key): value for key, value in raw_spec.items()
        }
    return snapshot


def _resolve_registry(raw: object) -> QueryTargetRegistry | None:
    if isinstance(raw, QueryTargetRegistry):
        return raw
    return get_query_target_registry()


def _sql_aliases(
    *,
    schema_snapshot: Mapping[str, dict[str, object]],
    query_target_registry: QueryTargetRegistry | None,
) -> list[str]:
    aliases: set[str] = set()
    if query_target_registry is not None:
        for alias in query_target_registry.aliases():
            target = query_target_registry.get(alias)
            if target is None:
                continue
            if str(target.engine or "").strip().lower() in {"postgres", "sqlite"}:
                aliases.add(alias)
    for spec in schema_snapshot.values():
        alias = str(spec.get("target_alias") or "").strip()
        if not alias:
            continue
        if query_target_registry is None:
            aliases.add(alias)
            continue
        target = query_target_registry.get(alias)
        if target is not None and str(target.engine or "").strip().lower() in {
            "postgres",
            "sqlite",
        }:
            aliases.add(alias)
    return sorted(aliases)


def _build_alias_context(
    *,
    alias: str,
    schema_snapshot: Mapping[str, dict[str, object]],
    query_target_registry: QueryTargetRegistry | None,
) -> str:
    engine = ""
    if query_target_registry is not None:
        target = query_target_registry.get(alias)
        if target is not None:
            engine = str(target.engine or "").strip().lower()

    lines: list[str] = [f"alias={alias}", f"engine={engine}"]
    for table_id, spec in sorted(schema_snapshot.items()):
        if str(spec.get("target_alias") or "").strip() != alias:
            continue
        table_name = str(spec.get("table_name") or "").strip()
        qualified_table_name = str(spec.get("qualified_table_name") or "").strip()
        description = str(spec.get("description") or "").strip()
        lines.append(f"- table_id={table_id}")
        lines.append(f"  qualified_table_name={qualified_table_name or table_name}")
        if description:
            lines.append(f"  description={description}")
        columns = spec.get("columns")
        column_descriptions = spec.get("column_descriptions")
        column_types = spec.get("column_types")
        if isinstance(columns, list) and columns:
            lines.append("  columns=")
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
                lines.append(
                    f"    - {column_name} | type={column_type or 'unknown'} | description={column_description}"
                )
    return "\n".join(lines).strip()


def _run_schema_selection_prepare_step(state: Mapping[str, Any]) -> dict[str, object]:
    """스키마 선택 입력 컨텍스트를 생성한다."""

    schema_snapshot = _to_schema_snapshot(state.get("schema_snapshot"))
    query_target_registry = _resolve_registry(state.get("query_target_registry"))
    aliases = _sql_aliases(
        schema_snapshot=schema_snapshot,
        query_target_registry=query_target_registry,
    )
    context_lines = [f"sql_target_aliases={aliases}"]
    for alias in aliases:
        context_lines.append(
            _build_alias_context(
                alias=alias,
                schema_snapshot=schema_snapshot,
                query_target_registry=query_target_registry,
            )
        )

    return {
        "schema_selection_context": "\n\n".join(
            line for line in context_lines if line
        ).strip(),
        "available_target_aliases": aliases,
        "selected_target_aliases": [],
        "sql_texts_by_alias": {},
        "sql_retry_feedbacks": {},
        "execution_reports": {},
        "retry_count_by_alias": {},
        "raw_sql_inputs": [],
        "success_aliases": [],
        "failed_aliases": [],
        "failure_codes": [],
        "failure_details": [],
        "sql_pipeline_failure_stage": "",
        "sql_pipeline_failure_details": [],
    }


schema_selection_prepare_node = function_node(
    fn=_run_schema_selection_prepare_step,
    node_name="schema_selection_prepare",
    logger=_schema_selection_prepare_logger,
)

__all__ = ["schema_selection_prepare_node"]
