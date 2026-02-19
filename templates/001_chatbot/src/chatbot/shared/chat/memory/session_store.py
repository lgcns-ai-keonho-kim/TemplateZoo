"""
목적: Chat 세션 메모리 저장소를 제공한다.
설명: Redis 리스트 명령과 유사한 rpush/lrange 기반으로 세션 메시지 캐시를 관리한다.
디자인 패턴: 저장소 패턴
참조: src/chatbot/shared/chat/services/chat_service.py, src/chatbot/core/chat/models/entities.py
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Callable

from chatbot.core.chat.models import ChatMessage
from chatbot.shared.logging import Logger, create_default_logger


class ChatSessionMemoryStore:
    """세션 메시지 메모리 저장소."""

    def __init__(
        self,
        max_messages: int = 200,
        logger: Logger | None = None,
    ) -> None:
        self._max_messages = max(1, max_messages)
        self._logger = logger or create_default_logger("ChatSessionMemoryStore")
        self._lock = threading.RLock()
        self._sessions: dict[str, deque[ChatMessage]] = {}

    @property
    def max_messages(self) -> int:
        """세션별 최대 보관 메시지 수를 반환한다."""

        return self._max_messages

    def has_session(self, session_id: str) -> bool:
        """세션 메모리 보유 여부를 반환한다."""

        with self._lock:
            return session_id in self._sessions

    def ensure_session(
        self,
        session_id: str,
        loader: Callable[[], list[ChatMessage]],
    ) -> None:
        """세션이 없으면 외부 loader로 초기화한다."""

        with self._lock:
            if session_id in self._sessions:
                return
        loaded = loader()
        with self._lock:
            if session_id in self._sessions:
                return
            copied = [self._copy_message(message) for message in loaded]
            self._sessions[session_id] = deque(
                copied[-self._max_messages :],
                maxlen=self._max_messages,
            )
        self._logger.debug(f"세션 메모리 초기화: session_id={session_id}, count={len(loaded)}")

    def replace_session(self, session_id: str, messages: list[ChatMessage]) -> None:
        """세션 메시지를 통째로 교체한다."""

        with self._lock:
            copied = [self._copy_message(message) for message in messages]
            self._sessions[session_id] = deque(
                copied[-self._max_messages :],
                maxlen=self._max_messages,
            )

    def rpush(self, session_id: str, message: ChatMessage) -> None:
        """세션 메시지 리스트 우측에 메시지를 추가한다."""

        with self._lock:
            bucket = self._sessions.get(session_id)
            if bucket is None:
                bucket = deque(maxlen=self._max_messages)
                self._sessions[session_id] = bucket
            bucket.append(self._copy_message(message))

    def lrange(self, session_id: str, start: int, end: int) -> list[ChatMessage]:
        """세션 메시지 리스트 범위를 조회한다.

        Redis `LRANGE`와 동일하게 start/end(포함 범위)를 해석한다.
        """

        with self._lock:
            source = list(self._sessions.get(session_id, deque()))
        size = len(source)
        if size == 0:
            return []
        normalized_start = self._normalize_index(start, size)
        normalized_end = self._normalize_index(end, size)
        if normalized_start >= size:
            return []
        normalized_end = min(normalized_end, size - 1)
        if normalized_start > normalized_end:
            return []
        return [self._copy_message(item) for item in source[normalized_start : normalized_end + 1]]

    def clear_session(self, session_id: str) -> None:
        """세션 메모리를 제거한다."""

        with self._lock:
            self._sessions.pop(session_id, None)

    def _normalize_index(self, index: int, size: int) -> int:
        if index < 0:
            return max(size + index, 0)
        return index

    def _copy_message(self, message: ChatMessage) -> ChatMessage:
        if hasattr(message, "model_copy"):
            return message.model_copy(deep=True)
        return ChatMessage(**message.model_dump(mode="python"))
