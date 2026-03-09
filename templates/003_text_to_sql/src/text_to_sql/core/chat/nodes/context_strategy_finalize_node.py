"""
목적: 컨텍스트 전략 후처리 노드를 제공한다.
설명: 정규화된 context_strategy를 기준으로 SQL 경로 진입 여부와 재사용 컨텍스트를 세팅한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/text_to_sql/core/chat/nodes/context_strategy_route_node.py, src/text_to_sql/shared/chat/nodes/function_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.core.chat.const import (
    METADATA_ROUTE_RESPONSE,
)
from text_to_sql.core.chat.nodes.context_strategy_node import (
    CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
    CONTEXT_STRATEGY_USE_METADATA,
    CONTEXT_STRATEGY_USE_SQL,
)
from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_context_strategy_finalize_logger: Logger = create_default_logger(
    "ContextStrategyFinalizeNode"
)

_REUSE_HINTS = (
    "이전 답변",
    "방금 답변",
    "위 답변",
    "앞서 답변",
    "요약",
    "다시 정리",
    "한줄",
    "한 줄",
    "핵심만",
    "짧게",
    "다듬어",
    "풀어서",
    "쉽게",
    "번역",
    "영어로",
    "한국어로",
)

_SQL_INTENT_HINTS = (
    "조회",
    "다시 조회",
    "검색",
    "필터",
    "정렬",
    "최신",
    "현재",
    "비교",
    "합계",
    "평균",
    "최대",
    "최소",
    "개수",
    "count",
    "sum",
    "avg",
    "max",
    "min",
    "group by",
    "join",
)

_MEANING_HINTS = (
    "의미",
    "뜻",
    "무슨 의미",
    "무슨 뜻",
    "정의",
    "설명",
    "뭐야",
    "무엇",
)


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)


def _should_force_reuse(user_message: str, has_last_assistant: bool) -> bool:
    if not has_last_assistant:
        return False
    normalized = str(user_message or "").strip().lower()
    if not normalized:
        return False
    has_reuse_hint = _contains_any(normalized, _REUSE_HINTS)
    has_sql_intent = _contains_any(normalized, _SQL_INTENT_HINTS)
    return has_reuse_hint and not has_sql_intent


def _is_meaning_query(user_message: str) -> bool:
    normalized = str(user_message or "").strip().lower()
    if not normalized:
        return False
    return _contains_any(normalized, _MEANING_HINTS)


def _normalize_answer_source_meta(raw: object) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return {}
    normalized = {str(key): value for key, value in raw.items()}
    column_ids = normalized.get("column_ids")
    if not isinstance(column_ids, list):
        normalized["column_ids"] = []
    return normalized


def _run_context_strategy_finalize_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """최종 전략을 확정하고 response/SQL 노드가 사용할 컨텍스트를 준비한다."""

    strategy = (
        str(state.get("context_strategy") or CONTEXT_STRATEGY_USE_SQL).strip().upper()
    )
    last_assistant_message = str(state.get("last_assistant_message") or "").strip()
    user_message = str(state.get("user_message") or "").strip()
    last_answer_source_meta = _normalize_answer_source_meta(
        state.get("last_answer_source_meta")
    )
    has_answer_source_meta = bool(last_answer_source_meta.get("column_ids"))

    if strategy not in {
        CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT,
        CONTEXT_STRATEGY_USE_METADATA,
        CONTEXT_STRATEGY_USE_SQL,
    }:
        strategy = CONTEXT_STRATEGY_USE_SQL

    if _is_meaning_query(user_message):
        strategy = (
            CONTEXT_STRATEGY_USE_METADATA
            if has_answer_source_meta
            else CONTEXT_STRATEGY_USE_SQL
        )

    if strategy == CONTEXT_STRATEGY_USE_METADATA:
        if has_answer_source_meta:
            return {
                "context_strategy": strategy,
                "metadata_route": METADATA_ROUTE_RESPONSE,
                "answer_source_meta": last_answer_source_meta,
                "sql_pipeline_failure_stage": "",
                "sql_pipeline_failure_details": [],
                "sql_answer_context": "",
            }
        return {
            "context_strategy": CONTEXT_STRATEGY_USE_SQL,
            "metadata_route": "sql",
            "answer_source_meta": {},
            "sql_pipeline_failure_stage": "",
            "sql_pipeline_failure_details": [],
            "sql_answer_context": "",
        }

    # 직전 assistant 답변이 없으면 재사용할 근거가 없으므로 강제로 USE_SQL을 사용한다.
    if not last_assistant_message:
        strategy = CONTEXT_STRATEGY_USE_SQL
    elif _should_force_reuse(user_message, bool(last_assistant_message)):
        strategy = CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT

    _context_strategy_finalize_logger.debug(
        "context.strategy.finalize: strategy=%s" % strategy
    )

    return {
        "context_strategy": strategy,
        "metadata_route": METADATA_ROUTE_RESPONSE,
        "answer_source_meta": {},
        "sql_answer_context": (
            last_assistant_message
            if strategy == CONTEXT_STRATEGY_REUSE_LAST_ASSISTANT
            else ""
        ),
        "sql_pipeline_failure_stage": "",
        "sql_pipeline_failure_details": [],
    }


context_strategy_finalize_node = function_node(
    fn=_run_context_strategy_finalize_step,
    node_name="context_strategy_finalize",
    logger=_context_strategy_finalize_logger,
)

__all__ = ["context_strategy_finalize_node"]
