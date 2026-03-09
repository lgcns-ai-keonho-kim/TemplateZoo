"""
목적: alias별 raw SQL 실행 결과를 최종 실행 컨텍스트로 수집한다.
설명: execution_reports를 성공/실패 집합과 사용자 노출용 실패 상세로 정규화한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/nodes/sql_answer_prepare_node.py
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_sql_result_collect_logger: Logger = create_default_logger("SQLResultCollectNode")


def _to_report_map(raw: object) -> dict[str, dict[str, object]]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, dict[str, object]] = {}
    for alias, item in raw.items():
        normalized_alias = str(alias).strip()
        if not normalized_alias or not isinstance(item, Mapping):
            continue
        result[normalized_alias] = {str(key): value for key, value in item.items()}
    return result


def _normalize_rows(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []
    return [
        {str(key): value for key, value in item.items()}
        for item in raw
        if isinstance(item, Mapping)
    ]


def _to_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _to_schema_snapshot(raw: object) -> dict[str, dict[str, object]]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, dict[str, object]] = {}
    for table_id, item in raw.items():
        normalized_table_id = str(table_id or "").strip()
        if not normalized_table_id or not isinstance(item, Mapping):
            continue
        result[normalized_table_id] = {str(key): value for key, value in item.items()}
    return result


def _extract_sql_column_tokens(sql_text: str) -> set[str]:
    normalized_sql = str(sql_text or "").strip()
    if not normalized_sql:
        return set()

    quoted = {
        str(match).strip()
        for match in re.findall(r'"([^"]+)"', normalized_sql)
        if str(match).strip()
    }
    plain = {
        str(match).strip()
        for match in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", normalized_sql)
        if str(match).strip()
    }
    return {token for token in quoted | plain if token}


def _build_answer_source_meta(
    *,
    schema_snapshot: Mapping[str, dict[str, object]],
    success_aliases: list[str],
    sql_by_alias: Mapping[str, str],
) -> dict[str, object]:
    if not success_aliases:
        return {}

    selected_aliases = {alias for alias in success_aliases if alias}
    sql_tokens: set[str] = set()
    for alias in selected_aliases:
        sql_tokens.update(_extract_sql_column_tokens(str(sql_by_alias.get(alias) or "")))

    table_ids: list[str] = []
    column_ids: list[str] = []
    column_descriptions: dict[str, str] = {}
    lineage: dict[str, str] = {}
    seen_column_ids: set[str] = set()
    plain_column_owners: dict[str, set[str]] = {}
    plain_column_descriptions: dict[str, str] = {}

    for table_id, spec in sorted(schema_snapshot.items()):
        target_alias = str(spec.get("target_alias") or "").strip()
        if target_alias not in selected_aliases:
            continue
        table_ids.append(table_id)

        raw_columns = spec.get("columns")
        columns = (
            [str(item).strip() for item in raw_columns if str(item).strip()]
            if isinstance(raw_columns, list)
            else []
        )
        raw_descriptions = spec.get("column_descriptions")
        descriptions = (
            {str(key): str(value) for key, value in raw_descriptions.items()}
            if isinstance(raw_descriptions, Mapping)
            else {}
        )

        for column_name in columns:
            qualified_id = f"{table_id}.{column_name}"
            should_include = not sql_tokens or column_name in sql_tokens
            if not should_include:
                continue
            if qualified_id not in seen_column_ids:
                seen_column_ids.add(qualified_id)
                column_ids.append(qualified_id)
            lineage[qualified_id] = column_name
            description = str(descriptions.get(column_name) or "").strip()
            if description:
                column_descriptions[qualified_id] = description
                plain_column_descriptions.setdefault(column_name, description)
            owners = plain_column_owners.setdefault(column_name, set())
            owners.add(table_id)

    for column_name, owners in sorted(plain_column_owners.items()):
        if len(owners) != 1:
            continue
        if column_name not in seen_column_ids:
            column_ids.append(column_name)
            seen_column_ids.add(column_name)
        lineage[column_name] = column_name
        description = plain_column_descriptions.get(column_name, "").strip()
        if description:
            column_descriptions[column_name] = description

    return {
        "table_ids": table_ids,
        "column_ids": column_ids,
        "column_descriptions": column_descriptions,
        "lineage": lineage,
    }


def _run_sql_result_collect_step(state: Mapping[str, Any]) -> dict[str, object]:
    """실행 결과를 최종 컨텍스트로 수집한다."""

    reports = _to_report_map(state.get("execution_reports"))
    success_aliases: list[str] = []
    failed_aliases: list[str] = []
    failure_details: list[dict[str, object]] = []
    failure_codes: list[str] = []
    total_rows = 0
    sample_rows_by_alias: dict[str, list[dict[str, object]]] = {}
    sql_by_alias: dict[str, str] = {}
    row_count_by_alias: dict[str, int] = {}
    schema_snapshot = _to_schema_snapshot(state.get("schema_snapshot"))

    for alias in sorted(reports.keys()):
        report = reports[alias]
        status = str(report.get("status") or "").strip().lower()
        sql_by_alias[alias] = str(report.get("sql") or "").strip()
        row_count = _to_int(report.get("row_count"))
        row_count_by_alias[alias] = row_count
        total_rows += row_count
        rows = _normalize_rows(report.get("rows"))
        sample_rows_by_alias[alias] = rows[:10]
        if status == "ok":
            success_aliases.append(alias)
            continue
        failed_aliases.append(alias)
        code = str(report.get("code") or "").strip()
        message = str(report.get("message") or "").strip()
        if code:
            failure_codes.append(code)
        failure_details.append(
            {
                "query_id": alias,
                "table_id": alias,
                "code": code,
                "message": message,
            }
        )

    answer_source_meta = _build_answer_source_meta(
        schema_snapshot=schema_snapshot,
        success_aliases=success_aliases,
        sql_by_alias=sql_by_alias,
    )

    return {
        "success_aliases": success_aliases,
        "failed_aliases": failed_aliases,
        "failure_codes": failure_codes,
        "failure_details": failure_details,
        "answer_source_meta": answer_source_meta,
        "sql_result": {
            "phase": "sql_result_collect",
            "success_alias_count": len(success_aliases),
            "failed_alias_count": len(failed_aliases),
            "row_count": total_rows,
            "selected_aliases": sorted(reports.keys()),
            "sql_by_alias": sql_by_alias,
            "row_count_by_alias": row_count_by_alias,
            "sample_rows_by_alias": sample_rows_by_alias,
            "answer_source_meta": answer_source_meta,
        },
    }


sql_result_collect_node = function_node(
    fn=_run_sql_result_collect_step,
    node_name="sql_result_collect",
    logger=_sql_result_collect_logger,
)

__all__ = ["sql_result_collect_node"]
