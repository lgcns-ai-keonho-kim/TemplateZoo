"""
목적: 스키마 선택 LLM 출력을 파싱한다.
설명: 쉼표 구분 alias 문자열을 정규화해 선택 alias 목록과 selection 실패 정보를 생성한다.
디자인 패턴: 함수 주입
참조: src/text_to_sql/core/chat/nodes/schema_selection_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_schema_selection_parse_logger: Logger = create_default_logger(
    "SchemaSelectionParseNode"
)


def _to_alias_list(raw: object) -> list[str]:
    if isinstance(raw, list):
        candidates = raw
    else:
        candidates = str(raw or "").split(",")
    result: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        alias = str(item or "").strip()
        if not alias or alias in seen:
            continue
        seen.add(alias)
        result.append(alias)
    return result


def _available_aliases(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item or "").strip() for item in raw if str(item or "").strip()]


def _run_schema_selection_parse_step(state: Mapping[str, Any]) -> dict[str, object]:
    """스키마 선택 결과를 파싱하고 검증한다."""

    raw_output = str(state.get("schema_selection_raw") or "").strip()
    available_aliases = _available_aliases(state.get("available_target_aliases"))
    available_set = set(available_aliases)
    selected_aliases = [
        alias for alias in _to_alias_list(raw_output) if alias in available_set
    ]

    if not selected_aliases:
        return {
            "selected_target_aliases": [],
            "sql_pipeline_failure_stage": "schema_selection",
            "sql_pipeline_failure_details": [
                {
                    "code": "TARGET_ALIAS_SELECTION_EMPTY",
                    "message": "LLM이 유효한 SQL target alias를 선택하지 못했습니다.",
                }
            ],
            "sql_plan": {
                "phase": "schema_selection",
                "available_aliases": available_aliases,
                "selected_aliases": [],
                "raw_output": raw_output,
            },
        }

    return {
        "selected_target_aliases": selected_aliases,
        "sql_pipeline_failure_stage": "",
        "sql_pipeline_failure_details": [],
        "sql_plan": {
            "phase": "schema_selection",
            "available_aliases": available_aliases,
            "selected_aliases": selected_aliases,
            "raw_output": raw_output,
        },
    }


schema_selection_parse_node = function_node(
    fn=_run_schema_selection_parse_step,
    node_name="schema_selection_parse",
    logger=_schema_selection_parse_logger,
)

__all__ = ["schema_selection_parse_node"]
