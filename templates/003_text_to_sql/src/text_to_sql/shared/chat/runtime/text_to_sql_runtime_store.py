"""
목적: Text-to-SQL 런타임 공유 상태 저장소를 제공한다.
설명: 그래프 state 직렬화 대상에서 제외해야 하는 객체(QueryTargetRegistry)를 모듈 전역으로 관리한다.
디자인 패턴: 모듈 싱글턴
참조: src/text_to_sql/api/chat/services/runtime.py, src/text_to_sql/core/chat/nodes/raw_sql_execute_node.py
"""

from __future__ import annotations

from text_to_sql.integrations.db import QueryTargetRegistry

_QUERY_TARGET_REGISTRY: QueryTargetRegistry | None = None


def set_query_target_registry(registry: QueryTargetRegistry | None) -> None:
    """Query target registry를 설정한다."""

    global _QUERY_TARGET_REGISTRY
    _QUERY_TARGET_REGISTRY = registry


def get_query_target_registry() -> QueryTargetRegistry | None:
    """현재 Query target registry를 반환한다."""

    return _QUERY_TARGET_REGISTRY


def clear_query_target_registry() -> None:
    """Query target registry를 제거한다."""

    set_query_target_registry(None)


__all__ = [
    "set_query_target_registry",
    "get_query_target_registry",
    "clear_query_target_registry",
]
