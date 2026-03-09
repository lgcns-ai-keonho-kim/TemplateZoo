"""
목적: raw SQL 재시도 입력을 준비한다.
설명: 실패한 alias만 다시 선택하고 오류 메시지를 재시도 피드백으로 전달한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/nodes/raw_sql_execute_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_raw_sql_retry_prepare_logger: Logger = create_default_logger("RawSQLRetryPrepareNode")


def _to_input_list(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []
    return [
        {str(key): value for key, value in item.items()}
        for item in raw
        if isinstance(item, Mapping)
    ]


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


def _to_retry_map(raw: object) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(alias).strip(): str(message or "").strip()
        for alias, message in raw.items()
        if str(alias).strip()
    }


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


def _run_raw_sql_retry_prepare_step(state: Mapping[str, Any]) -> dict[str, object]:
    """재시도 대상 alias 입력을 재구성한다."""

    inputs = _to_input_list(state.get("raw_sql_inputs"))
    reports = _to_report_map(state.get("execution_reports"))
    retry_feedbacks = _to_retry_map(state.get("sql_retry_feedbacks"))
    retry_count_by_alias = _to_retry_count_map(state.get("retry_count_by_alias"))

    retry_inputs: list[dict[str, object]] = []
    for item in inputs:
        alias = str(item.get("target_alias") or "").strip()
        if not alias:
            continue
        report = reports.get(alias, {})
        if str(report.get("status") or "").strip().lower() == "ok":
            continue
        retry_inputs.append(item)
        retry_count_by_alias[alias] = retry_count_by_alias.get(alias, 0) + 1

    return {
        "raw_sql_inputs": retry_inputs,
        "sql_retry_feedbacks": retry_feedbacks,
        "retry_count_by_alias": retry_count_by_alias,
    }


raw_sql_retry_prepare_node = function_node(
    fn=_run_raw_sql_retry_prepare_step,
    node_name="raw_sql_retry_prepare",
    logger=_raw_sql_retry_prepare_logger,
)

__all__ = ["raw_sql_retry_prepare_node"]
