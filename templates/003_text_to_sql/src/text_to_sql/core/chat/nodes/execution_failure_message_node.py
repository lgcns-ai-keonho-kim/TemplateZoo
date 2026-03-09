"""
목적: SQL 실행 실패를 사용자 노출 메시지로 변환하는 노드를 제공한다.
설명: 실패 상세 목록을 사람이 읽을 수 있는 실패 안내문으로 정규화한다.
디자인 패턴: 함수 주입(Function Injection)
참조: src/text_to_sql/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_execution_failure_message_logger: Logger = create_default_logger(
    "ExecutionFailureMessageNode"
)
def _normalize_failure_details(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []
    result: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        normalized = {str(key): value for key, value in item.items()}
        result.append(normalized)
    return result


def _normalize_failure_codes(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    ordered: list[str] = []
    seen: set[str] = set()
    for item in raw:
        code = str(item or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        ordered.append(code)
    return ordered


def _build_failure_lines(
    *,
    failure_details: list[dict[str, object]],
    failure_codes: list[str],
) -> list[str]:
    lines: list[str] = []
    for item in failure_details[:3]:
        query_id = str(item.get("query_id") or "").strip() or "q?"
        table_id = str(item.get("table_id") or "").strip()
        code = str(item.get("code") or "").strip() or "SQL_EXECUTION_FAILED"
        message = str(item.get("message") or "").strip() or "원인을 확인할 수 없습니다."
        table_text = f", table={table_id}" if table_id else ""
        lines.append(f"- query_id={query_id}{table_text}, code={code}, 원인={message}")
    if lines:
        return lines
    for code in failure_codes[:3]:
        lines.append(f"- code={code}, 원인=실행 실패 상세 메시지가 비어 있습니다.")
    if lines:
        return lines
    return [
        "- code=SQL_EXECUTION_FAILED, 원인=실행 실패 상세 정보를 확인할 수 없습니다."
    ]


def _run_execution_failure_message_step(state: Mapping[str, Any]) -> dict[str, str]:
    """실행 실패 상세를 assistant_message로 변환한다."""

    failure_details = _normalize_failure_details(state.get("failure_details"))
    failure_codes = _normalize_failure_codes(state.get("failure_codes"))
    message_lines = [
        "SQL 실행에 실패했습니다.",
        *_build_failure_lines(
            failure_details=failure_details,
            failure_codes=failure_codes,
        ),
    ]

    _execution_failure_message_logger.debug(
        "execution.failure.message: failure_count=%s"
        % len(failure_details or failure_codes)
    )
    return {"assistant_message": "\n".join(message_lines)}


execution_failure_message_node = function_node(
    fn=_run_execution_failure_message_step,
    node_name="execution_failure_message",
    logger=_execution_failure_message_logger,
)

__all__ = ["execution_failure_message_node"]
