"""
목적: 컨텍스트 전략 분류 입력 준비 노드를 제공한다.
설명: 히스토리에서 직전 assistant 답변을 추출해 LLM 분류 입력 키(last_assistant_message)로 기록한다.
디자인 패턴: 모듈 조립 + 함수 주입
참조: src/text_to_sql/core/chat/nodes/context_strategy_node.py, src/text_to_sql/core/chat/models/entities.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from text_to_sql.core.chat.models import ChatMessage
from text_to_sql.shared.chat.runtime import get_assistant_context_store
from text_to_sql.shared.chat.nodes import function_node
from text_to_sql.shared.logging import Logger, create_default_logger

_context_strategy_prepare_logger: Logger = create_default_logger(
    "ContextStrategyPrepareNode"
)


def _run_context_strategy_prepare_step(state: Mapping[str, Any]) -> dict[str, Any]:
    """히스토리에서 직전 assistant 답변을 찾아 state에 기록한다."""

    session_id = str(state.get("session_id") or "").strip()
    history = state.get("history")
    last_assistant_message = ""
    last_answer_source_meta: dict[str, Any] = {}
    if isinstance(history, list):
        for item in reversed(history):
            if isinstance(item, ChatMessage):
                if item.role.value != "assistant":
                    continue
                content = str(item.content or "").strip()
                if content:
                    last_assistant_message = content
                    raw_meta = item.metadata
                    if isinstance(raw_meta, Mapping):
                        source_meta = raw_meta.get("answer_source_meta")
                        if isinstance(source_meta, Mapping):
                            last_answer_source_meta = {
                                str(key): value for key, value in source_meta.items()
                            }
                    break
                continue

            if isinstance(item, Mapping):
                role = str(item.get("role") or "").strip().lower()
                if role != "assistant":
                    continue
                content = str(item.get("content") or "").strip()
                if content:
                    last_assistant_message = content
                    raw_meta = item.get("metadata")
                    if isinstance(raw_meta, Mapping):
                        source_meta = raw_meta.get("answer_source_meta")
                        if isinstance(source_meta, Mapping):
                            last_answer_source_meta = {
                                str(key): value for key, value in source_meta.items()
                            }
                    break

    # persist 비동기 구간에서 history 반영 전이라도 직전 assistant 컨텍스트를 보완한다.
    store = get_assistant_context_store()
    if store is not None and session_id:
        try:
            cached = store.get(session_id)
        except Exception as error:  # noqa: BLE001 - 캐시 조회 실패 시 history 기반 흐름 유지
            _context_strategy_prepare_logger.warning(
                "context.strategy.prepare: assistant_context 조회 실패: session_id=%s, error=%s"
                % (session_id, error)
            )
            cached = None
        if cached is not None:
            cached_content = str(cached.content or "").strip()
            if not last_assistant_message and cached_content:
                last_assistant_message = cached_content
            if not last_answer_source_meta and isinstance(
                cached.answer_source_meta, Mapping
            ):
                last_answer_source_meta = {
                    str(key): value for key, value in cached.answer_source_meta.items()
                }

    _context_strategy_prepare_logger.debug(
        "context.strategy.prepare: has_last_assistant=%s, has_answer_source_meta=%s, last_assistant_length=%s"
        % (
            bool(last_assistant_message),
            bool(last_answer_source_meta),
            len(last_assistant_message),
        )
    )

    metadata_table_count = 0
    metadata_column_count = 0
    if isinstance(last_answer_source_meta.get("table_ids"), list):
        metadata_table_count = len(last_answer_source_meta["table_ids"])
    if isinstance(last_answer_source_meta.get("column_ids"), list):
        metadata_column_count = len(last_answer_source_meta["column_ids"])

    metadata_summary = (
        f"has_answer_source_meta={'true' if last_answer_source_meta else 'false'}; "
        f"table_count={metadata_table_count}; "
        f"column_count={metadata_column_count}"
    )

    return {
        "last_assistant_message": last_assistant_message,
        "last_answer_source_meta": last_answer_source_meta,
        "metadata_summary": metadata_summary,
    }


context_strategy_prepare_node = function_node(
    fn=_run_context_strategy_prepare_step,
    node_name="context_strategy_prepare",
    logger=_context_strategy_prepare_logger,
)

__all__ = ["context_strategy_prepare_node"]
