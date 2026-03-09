"""
목적: assistant 컨텍스트 캐시 런타임 공유 상태 API를 제공한다.
설명: 세션별 직전 assistant 컨텍스트 저장소를 모듈 전역으로 관리한다.
디자인 패턴: 모듈 싱글턴
참조: src/text_to_sql/api/chat/services/runtime.py, src/text_to_sql/core/chat/nodes/context_strategy_prepare_node.py
"""

from __future__ import annotations

from text_to_sql.shared.chat.runtime.assistant_context import AssistantContextStore

_ASSISTANT_CONTEXT_STORE: AssistantContextStore | None = None


def set_assistant_context_store(store: AssistantContextStore | None) -> None:
    """assistant 컨텍스트 캐시 저장소를 설정한다."""

    global _ASSISTANT_CONTEXT_STORE
    _ASSISTANT_CONTEXT_STORE = store


def get_assistant_context_store() -> AssistantContextStore | None:
    """현재 assistant 컨텍스트 캐시 저장소를 반환한다."""

    return _ASSISTANT_CONTEXT_STORE


def clear_assistant_context(session_id: str) -> None:
    """세션별 assistant 컨텍스트를 제거한다."""

    store = _ASSISTANT_CONTEXT_STORE
    if store is None:
        return
    store.clear_session(session_id=session_id)


def close_assistant_context_store() -> None:
    """assistant 컨텍스트 캐시 저장소를 정리한다."""

    global _ASSISTANT_CONTEXT_STORE
    store = _ASSISTANT_CONTEXT_STORE
    _ASSISTANT_CONTEXT_STORE = None
    if store is None:
        return
    store.close()


__all__ = [
    "set_assistant_context_store",
    "get_assistant_context_store",
    "clear_assistant_context",
    "close_assistant_context_store",
]
