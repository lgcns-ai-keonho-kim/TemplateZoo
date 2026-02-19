"""
목적: Chat 코어 실행 서비스를 제공한다.
설명: 세션/메시지 저장소와 ChatGraph 실행을 결합한다.
디자인 패턴: 서비스 레이어
참조: src/chatbot/shared/chat/graph/base_chat_graph.py, src/chatbot/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

from chatbot.core.chat.const import DEFAULT_CONTEXT_WINDOW
from chatbot.core.chat.models import ChatMessage, ChatRole, ChatSession
from chatbot.shared.chat.interface import ChatServicePort, GraphPort
from chatbot.shared.chat.memory import ChatSessionMemoryStore
from chatbot.shared.chat.repositories import ChatHistoryRepository
from chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from chatbot.shared.logging import Logger, create_default_logger


class ChatService(ChatServicePort):
    """Chat 코어 실행 서비스."""

    def __init__(
        self,
        graph: GraphPort,
        repository: ChatHistoryRepository | None = None,
        memory_store: ChatSessionMemoryStore | None = None,
        logger: Logger | None = None,
    ) -> None:
        self._logger = logger or create_default_logger("CoreChatService")
        self._repository = repository or ChatHistoryRepository(logger=self._logger)
        self._memory_limit = max(1, int(os.getenv("CHAT_MEMORY_MAX_MESSAGES", "200")))
        self._memory_store = memory_store or ChatSessionMemoryStore(
            max_messages=self._memory_limit,
            logger=self._logger,
        )
        self._graph = graph

    @property
    def memory_store(self) -> ChatSessionMemoryStore:
        return self._memory_store

    def close(self) -> None:
        self._repository.close()

    def create_session(
        self,
        session_id: str | None = None,
        title: str | None = None,
    ) -> ChatSession:
        session = self._repository.create_session(session_id=session_id, title=title)
        self._ensure_memory_loaded(session.session_id)
        return session

    def list_sessions(self, limit: int, offset: int) -> list[ChatSession]:
        return self._repository.list_sessions(limit=limit, offset=offset)

    def get_session(self, session_id: str) -> ChatSession | None:
        return self._repository.get_session(session_id)

    def list_messages(self, session_id: str, limit: int, offset: int) -> list[ChatMessage]:
        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={session_id}")
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        return self._repository.list_messages(session_id=session_id, limit=limit, offset=offset)

    def delete_session(self, session_id: str) -> None:
        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={session_id}")
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        deleted, _ = self._repository.delete_session(session_id=session_id)
        if not deleted:
            detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={session_id}")
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        self._memory_store.clear_session(session_id=session_id)

    def invoke(
        self,
        session_id: str,
        user_query: str,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
    ) -> ChatMessage:
        user_message = self._append_user_message_existing_session(session_id=session_id, message=user_query)
        history = self._build_context_history(
            session_id=session_id,
            context_window=context_window,
            exclude_message_id=user_message.message_id,
            max_sequence=user_message.sequence - 1,
        )
        content = self._graph.invoke(
            session_id=session_id,
            user_message=user_message.content,
            history=history,
            config=self._cfg(session_id),
        )
        if not content:
            detail = ExceptionDetail(code="CHAT_STREAM_EMPTY", cause="invoke returned empty content")
            raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)
        return self.append_assistant_message(session_id=session_id, content=content)

    async def ainvoke(
        self,
        session_id: str,
        user_query: str,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
    ) -> ChatMessage:
        user_message = self._append_user_message_existing_session(session_id=session_id, message=user_query)
        history = self._build_context_history(
            session_id=session_id,
            context_window=context_window,
            exclude_message_id=user_message.message_id,
            max_sequence=user_message.sequence - 1,
        )
        content = await self._graph.ainvoke(
            session_id=session_id,
            user_message=user_message.content,
            history=history,
            config=self._cfg(session_id),
        )
        if not content:
            detail = ExceptionDetail(code="CHAT_STREAM_EMPTY", cause="ainvoke returned empty content")
            raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)
        return self.append_assistant_message(session_id=session_id, content=content)

    def stream(
        self,
        session_id: str,
        user_query: str,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
    ) -> Iterator[dict[str, Any]]:
        user_message = self._append_user_message_existing_session(session_id=session_id, message=user_query)
        history = self._build_context_history(
            session_id=session_id,
            context_window=context_window,
            exclude_message_id=user_message.message_id,
            max_sequence=user_message.sequence - 1,
        )

        chunks: list[str] = []
        fallback_content = ""
        done_node = "response"
        for event in self._graph.stream_events(
            session_id=session_id,
            user_message=user_message.content,
            history=history,
            config=self._cfg(session_id),
        ):
            node = str(event.get("node") or "").strip()
            event_name = str(event.get("event") or "").strip()
            data = event.get("data")
            if event_name == "token":
                text = str(data or "")
                if text:
                    chunks.append(text)
                    done_node = node or done_node
            if event_name == "assistant_message":
                candidate = str(data or "")
                if candidate.strip():
                    fallback_content = candidate
                    done_node = node or done_node
            yield {"node": node, "event": event_name, "data": data}

        final_content = "".join(chunks)
        if not final_content.strip():
            final_content = fallback_content
        if not final_content.strip():
            detail = ExceptionDetail(code="CHAT_STREAM_EMPTY", cause="stream returned empty content")
            raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)
        yield {
            "node": done_node or "response",
            "event": "done",
            "data": final_content,
        }

    async def astream(
        self,
        session_id: str,
        user_query: str,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
    ) -> AsyncIterator[dict[str, Any]]:
        user_message = self._append_user_message_existing_session(session_id=session_id, message=user_query)
        history = self._build_context_history(
            session_id=session_id,
            context_window=context_window,
            exclude_message_id=user_message.message_id,
            max_sequence=user_message.sequence - 1,
        )

        chunks: list[str] = []
        fallback_content = ""
        done_node = "response"
        async for event in self._graph.astream_events(
            session_id=session_id,
            user_message=user_message.content,
            history=history,
            config=self._cfg(session_id),
        ):
            node = str(event.get("node") or "").strip()
            event_name = str(event.get("event") or "").strip()
            data = event.get("data")
            if event_name == "token":
                text = str(data or "")
                if text:
                    chunks.append(text)
                    done_node = node or done_node
            if event_name == "assistant_message":
                candidate = str(data or "")
                if candidate.strip():
                    fallback_content = candidate
                    done_node = node or done_node
            yield {"node": node, "event": event_name, "data": data}

        final_content = "".join(chunks)
        if not final_content.strip():
            final_content = fallback_content
        if not final_content.strip():
            detail = ExceptionDetail(code="CHAT_STREAM_EMPTY", cause="astream returned empty content")
            raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)
        yield {
            "node": done_node or "response",
            "event": "done",
            "data": final_content,
        }

    def persist_assistant_message(
        self,
        session_id: str,
        request_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """assistant 응답을 request_id 멱등성 기준으로 1회 저장한다."""

        if self._repository.is_request_committed(request_id=request_id):
            self._logger.info(
                f"chat.persist.skip: session_id={session_id}, request_id={request_id}, reason=already_committed"
            )
            return False

        assistant_message = self.append_assistant_message(
            session_id=session_id,
            content=content,
            metadata=metadata,
        )
        self._repository.mark_request_committed(
            request_id=request_id,
            session_id=session_id,
            message_id=assistant_message.message_id,
        )
        return True

    def append_assistant_message(
        self,
        session_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessage:
        normalized = self._normalize_message(content)
        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={session_id}")
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        self._ensure_memory_loaded(session_id=session_id)
        assistant_message = self._repository.append_message(
            session_id=session_id,
            role=ChatRole.ASSISTANT,
            content=normalized,
            metadata=metadata,
        )
        self._memory_store.rpush(session_id=session_id, message=assistant_message)
        return assistant_message

    def _append_user_message_existing_session(self, session_id: str, message: str) -> ChatMessage:
        normalized = self._normalize_message(message)
        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={session_id}")
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        self._ensure_memory_loaded(session_id=session_id)
        user_message = self._repository.append_message(
            session_id=session_id,
            role=ChatRole.USER,
            content=normalized,
        )
        self._memory_store.rpush(session_id=session_id, message=user_message)
        return user_message

    def _cfg(self, session_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": session_id}}

    def _build_context_history(
        self,
        session_id: str,
        context_window: int,
        exclude_message_id: str | None = None,
        max_sequence: int | None = None,
    ) -> list[ChatMessage]:
        window = max(context_window, 1)
        recent = self._memory_store.lrange(
            session_id=session_id,
            start=-(window + 1),
            end=-1,
        )
        filtered = [
            item
            for item in recent
            if item.message_id != exclude_message_id
            and (max_sequence is None or item.sequence <= max_sequence)
        ]
        if len(filtered) > window:
            return filtered[-window:]
        return filtered

    def _ensure_memory_loaded(self, session_id: str) -> None:
        self._memory_store.ensure_session(
            session_id=session_id,
            loader=lambda: self._repository.get_recent_messages(
                session_id=session_id,
                limit=self._memory_store.max_messages,
            ),
        )

    def _normalize_message(self, message: str) -> str:
        raw = str(message or "")
        if not raw.strip():
            detail = ExceptionDetail(code="CHAT_MESSAGE_EMPTY", cause="message is empty")
            raise BaseAppException("메시지는 비어 있을 수 없습니다.", detail)
        return raw
