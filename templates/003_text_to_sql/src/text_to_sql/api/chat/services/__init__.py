"""
목적: Chat API 서비스 공개 API를 제공한다.
설명: Chat 실행 의존성과 의존성 주입 함수를 재노출한다.
디자인 패턴: 퍼사드
참조: src/text_to_sql/api/chat/services/runtime.py
"""

from text_to_sql.api.chat.services.runtime import (
    chat_service,
    get_chat_service,
    get_service_executor,
    get_text_to_sql_runtime_context,
    initialize_text_to_sql_runtime,
    service_executor,
    shutdown_chat_api_service,
)

__all__ = [
    "chat_service",
    "service_executor",
    "get_chat_service",
    "get_service_executor",
    "initialize_text_to_sql_runtime",
    "get_text_to_sql_runtime_context",
    "shutdown_chat_api_service",
]
