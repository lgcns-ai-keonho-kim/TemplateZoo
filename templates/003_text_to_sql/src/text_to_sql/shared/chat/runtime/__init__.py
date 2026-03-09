"""
목적: Text-to-SQL 런타임 공유 상태 API를 제공한다.
설명: QueryTargetRegistry와 assistant 컨텍스트 캐시 저장소의 설정/조회/정리 함수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/shared/chat/runtime/text_to_sql_runtime_store.py, src/text_to_sql/shared/chat/runtime/assistant_context_runtime_store.py
"""

from text_to_sql.shared.chat.runtime.assistant_context import (
    AssistantContext,
    AssistantContextStore,
    InMemoryAssistantContextStore,
    RedisAssistantContextStore,
)
from text_to_sql.shared.chat.runtime.assistant_context_runtime_store import (
    clear_assistant_context,
    close_assistant_context_store,
    get_assistant_context_store,
    set_assistant_context_store,
)
from text_to_sql.shared.chat.runtime.text_to_sql_runtime_store import (
    clear_query_target_registry,
    get_query_target_registry,
    set_query_target_registry,
)

__all__ = [
    "AssistantContext",
    "AssistantContextStore",
    "InMemoryAssistantContextStore",
    "RedisAssistantContextStore",
    "set_assistant_context_store",
    "get_assistant_context_store",
    "clear_assistant_context",
    "close_assistant_context_store",
    "set_query_target_registry",
    "get_query_target_registry",
    "clear_query_target_registry",
]
