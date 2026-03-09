"""
목적: 스키마 선택/SQL 생성 실패 메시지 노드를 제공한다.
설명: selection 또는 generation 단계의 실패 상세를 사용자 노출 메시지로 정규화한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_sql_pipeline_failure_logger: Logger = create_default_logger(
    "SQLPipelineFailureMessageNode"
)


def _normalize_details(raw: object) -> list[dict[str, object]]:
    if not isinstance(raw, list):
        return []
    result: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        result.append({str(key): value for key, value in item.items()})
    return result


def _headline(stage: str) -> str:
    if stage == "schema_selection":
        return "대상 스키마 선택에 실패했습니다."
    if stage == "metadata":
        return "이전 SQL 실행 근거가 없어 후속 설명 답변을 생성할 수 없습니다."
    if stage == "sql_generation":
        return "SQL 생성에 실패했습니다."
    return "SQL 파이프라인 처리에 실패했습니다."


def _run_sql_pipeline_failure_message_step(
    state: Mapping[str, Any],
) -> dict[str, str]:
    """파이프라인 실패 메시지를 생성한다."""

    stage = str(state.get("sql_pipeline_failure_stage") or "").strip()
    details = _normalize_details(state.get("sql_pipeline_failure_details"))
    lines = [_headline(stage)]
    for item in details[:3]:
        alias = str(item.get("target_alias") or "").strip()
        code = str(item.get("code") or "").strip() or "SQL_PIPELINE_FAILED"
        message = str(item.get("message") or "").strip() or "원인을 확인할 수 없습니다."
        alias_text = f"alias={alias}, " if alias else ""
        lines.append(f"- {alias_text}code={code}, 원인={message}")
    if len(lines) == 1:
        lines.append("- code=SQL_PIPELINE_FAILED, 원인=실패 상세 정보가 비어 있습니다.")
    return {"assistant_message": "\n".join(lines)}


sql_pipeline_failure_message_node = function_node(
    fn=_run_sql_pipeline_failure_message_step,
    node_name="sql_pipeline_failure_message",
    logger=_sql_pipeline_failure_logger,
)

__all__ = ["sql_pipeline_failure_message_node"]
