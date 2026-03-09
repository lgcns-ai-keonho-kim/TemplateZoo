"""
목적: alias별 raw SQL 실행 노드를 제공한다.
설명: 생성된 SQL을 선택 alias별로 실행하고 성공/실패 결과와 재시도 피드백을 정규화한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/shared/chat/nodes/raw_sql_executor.py
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from text_to_sql.integrations.db import QueryTargetRegistry
from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.chat.nodes.raw_sql_executor import RawSQLExecutor
from text_to_sql.shared.chat.runtime import get_query_target_registry
from text_to_sql.shared.logging import Logger, create_default_logger

_raw_sql_execute_logger: Logger = create_default_logger("RawSQLExecuteNode")
_raw_sql_executor = RawSQLExecutor(logger=create_default_logger("RawSQLExecutor"))


def _resolve_registry(raw: object) -> QueryTargetRegistry | None:
    if isinstance(raw, QueryTargetRegistry):
        return raw
    return get_query_target_registry()


def _to_input_list(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []
    return [
        {str(key): value for key, value in item.items()}
        for item in raw
        if isinstance(item, Mapping)
    ]


def _to_sql_map(raw: object) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(alias).strip(): str(sql or "").strip()
        for alias, sql in raw.items()
        if str(alias).strip()
    }


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


def _to_retry_count_map(raw: object) -> dict[str, int]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, int] = {}
    for alias, value in raw.items():
        normalized_alias = str(alias).strip()
        if not normalized_alias:
            continue
        result[normalized_alias] = _to_int(value)
    return result


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


def _build_retry_feedback(report: Mapping[str, Any]) -> str:
    code = str(report.get("code") or "").strip()
    message = str(report.get("message") or "").strip()
    sql = str(report.get("sql") or "").strip()
    return (
        "이전 SQL 실행이 실패했습니다. "
        f"오류코드={code}. 오류메시지={message}. 직전SQL={sql}"
    ).strip()


async def _run_raw_sql_execute_step(state: Mapping[str, Any]) -> dict[str, object]:
    """현재 배치의 raw SQL을 실행한다."""

    inputs = _to_input_list(state.get("raw_sql_inputs"))
    sql_texts_by_alias = _to_sql_map(state.get("sql_texts_by_alias"))
    existing_reports = _to_report_map(state.get("execution_reports"))
    retry_count_by_alias = _to_retry_count_map(state.get("retry_count_by_alias"))
    query_target_registry = _resolve_registry(state.get("query_target_registry"))

    alias_batches_by_client: dict[int, list[str]] = {}
    alias_order: list[str] = []
    for item in inputs:
        alias = str(item.get("target_alias") or "").strip()
        if not alias:
            continue
        alias_order.append(alias)
        client_key = hash(alias)
        if query_target_registry is not None:
            target = query_target_registry.get(alias)
            if target is not None:
                client_key = id(target.client)
        alias_batches_by_client.setdefault(client_key, []).append(alias)

    async def _execute_alias_batch(aliases: list[str]) -> list[tuple[str, dict[str, object]]]:
        batch_results: list[tuple[str, dict[str, object]]] = []
        for alias in aliases:
            sql = sql_texts_by_alias.get(alias, "")
            report = await asyncio.to_thread(
                _raw_sql_executor.execute,
                target_alias=alias,
                sql=sql,
                query_target_registry=query_target_registry,
            )
            batch_results.append((alias, report))
        return batch_results

    grouped_results = await asyncio.gather(
        *[
            _execute_alias_batch(aliases)
            for aliases in alias_batches_by_client.values()
        ],
        return_exceptions=False,
    )

    batch_reports: dict[str, dict[str, object]] = {}
    for grouped_batch in grouped_results:
        for alias, report in grouped_batch:
            batch_reports[alias] = report

    retry_feedbacks: dict[str, str] = {}
    failed_aliases: list[str] = []
    success_aliases: list[str] = []
    total_rows = 0
    for alias in alias_order:
        report = batch_reports.get(alias)
        if report is None:
            continue
        existing_reports[alias] = report
        total_rows += _to_int(report.get("row_count"))
        if str(report.get("status") or "").strip().lower() == "ok":
            success_aliases.append(alias)
            continue
        failed_aliases.append(alias)
        if retry_count_by_alias.get(alias, 0) <= 0:
            retry_feedbacks[alias] = _build_retry_feedback(report)

    payload_reports = []
    for alias in alias_order:
        report = batch_reports.get(alias)
        if report is None:
            continue
        payload_reports.append(
            {
                "target_alias": alias,
                "status": str(report.get("status") or "").strip(),
                "code": str(report.get("code") or "").strip(),
                "message": str(report.get("message") or "").strip(),
                "row_count": _to_int(report.get("row_count")),
            }
        )

    return {
        "execution_reports": existing_reports,
        "sql_retry_feedbacks": retry_feedbacks,
        "sql_result": {
            "phase": "raw_sql_execute",
            "success_alias_count": len(success_aliases),
            "failed_alias_count": len(failed_aliases),
            "row_count": total_rows,
            "reports": payload_reports,
        },
    }


raw_sql_execute_node = function_node(
    fn=_run_raw_sql_execute_step,
    node_name="raw_sql_execute",
    logger=_raw_sql_execute_logger,
)
raw_sql_execute_retry_node = function_node(
    fn=_run_raw_sql_execute_step,
    node_name="raw_sql_execute_retry",
    logger=_raw_sql_execute_logger,
)

__all__ = ["raw_sql_execute_node", "raw_sql_execute_retry_node"]
