"""
목적: Planner JSON 파서 유틸을 제공한다.
설명: LLM 출력에서 JSON 객체 후보를 추출하고 복구 파싱까지 수행한다.
디자인 패턴: 유틸리티
참조: src/plan_and_then_execute_agent/core/chat/nodes/_plan_utils.py
"""

from __future__ import annotations

import json
from typing import Any

from json_repair import repair_json

from plan_and_then_execute_agent.shared.exceptions import BaseAppException, ExceptionDetail


def parse_plan_json(raw: str) -> dict[str, Any]:
    """LLM 출력 문자열을 계획 JSON 객체로 파싱한다."""

    text = str(raw or "").strip()
    if not text:
        detail = ExceptionDetail(code="PLAN_JSON_EMPTY", cause="plan_raw is empty")
        raise BaseAppException("계획(JSON) 출력이 비어 있습니다.", detail)

    candidate = _extract_json_candidate(text)
    parsed = _try_load_json_object(candidate)
    if parsed is not None:
        return parsed

    repaired = repair_json(candidate, return_objects=True)
    if isinstance(repaired, tuple):
        repaired = repaired[0]
    if isinstance(repaired, dict):
        return {str(key): value for key, value in repaired.items()}

    detail = ExceptionDetail(
        code="PLAN_JSON_INVALID",
        cause="planner output is not a valid JSON object",
    )
    raise BaseAppException("계획(JSON) 파싱에 실패했습니다.", detail)


def _extract_json_candidate(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _try_load_json_object(text: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(loaded, dict):
        return None
    return {str(key): value for key, value in loaded.items()}

