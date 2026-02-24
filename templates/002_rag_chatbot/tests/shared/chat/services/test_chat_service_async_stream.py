"""
목적: ChatService 비동기 스트림 동작을 검증한다.
설명: 그래프 astream_events를 소비해 references/done 이벤트를 생성하는지 테스트한다.
디자인 패턴: 서비스 레이어 단위 테스트
참조: src/rag_chatbot/shared/chat/services/chat_service.py
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rag_chatbot.core.chat.models import ChatMessage, ChatRole, ChatSession
from rag_chatbot.shared.chat.memory import ChatSessionMemoryStore
from rag_chatbot.shared.chat.services.chat_service import ChatService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _GraphStub:
    async def astream_events(
        self,
        session_id: str,
        user_message: str,
        history: list[object],
        config: dict[str, object] | None = None,
    ):
        del session_id, user_message, history, config
        yield {"node": "response", "event": "token", "data": "안녕"}
        yield {"node": "response", "event": "token", "data": "하세요"}
        yield {
            "node": "rag_format",
            "event": "rag_references",
            "data": [
                {
                    "type": "reference",
                    "content": "본문",
                    "metadata": {"index": 1, "file_name": "manual.pdf"},
                }
            ],
        }


class _RepositoryStub:
    def __init__(self) -> None:
        self._session = ChatSession(
            session_id="s-1",
            title="테스트",
            created_at=_utc_now(),
            updated_at=_utc_now(),
            message_count=0,
        )
        self._messages: list[ChatMessage] = []
        self._sequence = 0

    def close(self) -> None:
        return

    def get_session(self, session_id: str) -> ChatSession | None:
        if session_id != self._session.session_id:
            return None
        return self._session

    def append_message(
        self,
        session_id: str,
        role: ChatRole,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> ChatMessage:
        self._sequence += 1
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sequence=self._sequence,
            created_at=_utc_now(),
            metadata={} if metadata is None else metadata,
        )
        self._messages.append(message)
        return message

    def get_recent_messages(self, session_id: str, limit: int) -> list[ChatMessage]:
        if session_id != self._session.session_id:
            return []
        return self._messages[-max(1, int(limit)) :]


@pytest.mark.asyncio
async def test_chat_service_astream_emits_references_and_done() -> None:
    """비동기 스트림 완료 시 references/done 이벤트가 생성되어야 한다."""

    repository = _RepositoryStub()
    service = ChatService(
        graph=_GraphStub(),
        repository=repository,  # type: ignore[arg-type]
        memory_store=ChatSessionMemoryStore(max_messages=20),
    )

    events = [
        event
        async for event in service.astream(
            session_id="s-1",
            user_query="테스트 질문",
            context_window=20,
        )
    ]

    types = [str(item.get("event") or "") for item in events]
    assert types == ["token", "token", "references", "done"]
    assert events[-1]["data"] == "안녕하세요"
    assert isinstance(events[2]["data"], list)
