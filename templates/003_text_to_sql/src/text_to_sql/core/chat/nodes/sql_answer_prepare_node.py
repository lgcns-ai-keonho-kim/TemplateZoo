"""
목적: raw SQL 실행 결과를 응답용 컨텍스트로 변환한다.
설명: alias별 실행 SQL, 행 수, 샘플 행을 문자열로 정규화해 response LLM의 입력으로 전달한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/nodes/response_node.py
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_sql_answer_prepare_logger: Logger = create_default_logger("SQLAnswerPrepareNode")


def _to_map(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


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


def _run_sql_answer_prepare_step(state: Mapping[str, Any]) -> dict[str, str]:
    """response LLM용 sql_answer_context를 생성한다."""

    reports = _to_map(state.get("execution_reports"))
    lines: list[str] = []
    total_rows = sum(
        _to_int(_to_map(report).get("row_count")) for report in reports.values()
    )
    lines.append(f"total_row_count={total_rows}")

    for alias in sorted(reports.keys()):
        report = _to_map(reports[alias])
        status = str(report.get("status") or "").strip().lower()
        if status != "ok":
            continue
        sql = str(report.get("sql") or "").strip()
        rows = _normalize_rows(report.get("rows"))
        lines.append(f"alias={alias}")
        lines.append(f"status=ok")
        lines.append(f"row_count={_to_int(report.get('row_count'))}")
        lines.append(f"sql={sql}")
        lines.append(
            "rows_json=" + json.dumps(rows[:20], ensure_ascii=False, default=str)
        )
        lines.append("")

    return {"sql_answer_context": "\n".join(lines).strip()}


sql_answer_prepare_node = function_node(
    fn=_run_sql_answer_prepare_step,
    node_name="sql_answer_prepare",
    logger=_sql_answer_prepare_logger,
)

__all__ = ["sql_answer_prepare_node"]
