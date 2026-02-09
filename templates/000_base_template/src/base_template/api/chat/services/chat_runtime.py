"""
목적: Chat 런타임 오케스트레이터를 제공한다.
설명: 대화 이력 저장소와 LangGraph를 조합해 사용자 턴을 처리한다.
디자인 패턴: 오케스트레이터 패턴
참조: src/base_template/core/repositories/chat/history_repository.py, src/base_template/core/chat/graphs/chat_graph.py, src/base_template/core/common/memory/session_list_store.py
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from base_template.core.common.memory import ChatSessionMemoryStore
from base_template.core.chat.const import DEFAULT_CONTEXT_WINDOW
from base_template.core.chat.graphs import ChatGraph
from base_template.core.chat.models import ChatMessage, ChatRole, ChatSession, ChatTurnResult
from base_template.core.repositories.chat import ChatHistoryRepository
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger


class ChatRuntime:
    """Chat 오케스트레이션 런타임."""

    def __init__(
        self,
        repository: Optional[ChatHistoryRepository] = None,
        graph: Optional[ChatGraph] = None,
        memory_store: Optional[ChatSessionMemoryStore] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._logger = logger or create_default_logger("ChatRuntime")
        self._repository = repository or ChatHistoryRepository(logger=self._logger)
        self._graph = graph or ChatGraph(logger=self._logger)
        self._memory_limit = max(1, int(os.getenv("CHAT_MEMORY_MAX_MESSAGES", "200")))
        self._memory_store = memory_store or ChatSessionMemoryStore(
            max_messages=self._memory_limit,
            logger=self._logger,
        )

    @property
    def memory_store(self) -> ChatSessionMemoryStore:
        """세션 메모리 저장소를 반환한다."""

        return self._memory_store

    def close(self) -> None:
        """내부 리소스를 정리한다."""

        self._repository.close()

    def create_session(
        self,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ChatSession:
        """세션을 생성하거나 지정한 식별자로 신규 생성한다."""

        session = self._repository.create_session(session_id=session_id, title=title)
        self._ensure_memory_loaded(session_id=session.session_id)
        return session

    def list_sessions(self, limit: int, offset: int) -> list[ChatSession]:
        """세션 목록을 조회한다."""

        return self._repository.list_sessions(limit=limit, offset=offset)

    def get_session(self, session_id: str) -> ChatSession | None:
        """세션 1건을 조회한다."""

        return self._repository.get_session(session_id)

    def delete_session(self, session_id: str) -> None:
        """세션과 메시지 이력을 삭제하고 메모리 캐시를 정리한다."""

        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(
                code="CHAT_SESSION_NOT_FOUND",
                cause=f"session_id={session_id}",
            )
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        deleted, deleted_message_count = self._repository.delete_session(session_id=session_id)
        if not deleted:
            detail = ExceptionDetail(
                code="CHAT_SESSION_NOT_FOUND",
                cause=f"session_id={session_id}",
            )
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        self._memory_store.clear_session(session_id=session_id)
        self._logger.info(
            f"세션 삭제 완료: session_id={session_id}, deleted_messages={deleted_message_count}"
        )

    def list_messages(self, session_id: str, limit: int, offset: int) -> list[ChatMessage]:
        """세션 메시지 목록을 조회한다."""

        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(
                code="CHAT_SESSION_NOT_FOUND",
                cause=f"session_id={session_id}",
            )
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        return self._repository.list_messages(session_id=session_id, limit=limit, offset=offset)

    def send_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
    ) -> ChatTurnResult:
        """사용자 메시지를 처리하고 어시스턴트 답변까지 저장한다."""

        session, user_message = self.append_user_message(
            message=message,
            session_id=session_id,
            title=title,
        )
        assistant_message = self.process_enqueued_turn(
            session_id=session.session_id,
            user_message_id=user_message.message_id,
            user_message_content=user_message.content,
            user_sequence=user_message.sequence,
            context_window=context_window,
        )
        return self._build_turn_result(session, user_message, assistant_message)

    def send_message_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> ChatTurnResult:
        """사용자 메시지를 처리하고 LLM 토큰 스트림을 전달하면서 결과를 저장한다."""

        session, user_message = self.append_user_message(
            message=message,
            session_id=session_id,
            title=title,
        )
        assistant_message = self.process_enqueued_turn(
            session_id=session.session_id,
            user_message_id=user_message.message_id,
            user_message_content=user_message.content,
            user_sequence=user_message.sequence,
            context_window=context_window,
            on_chunk=on_chunk,
        )
        return self._build_turn_result(session, user_message, assistant_message)

    def append_user_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> tuple[ChatSession, ChatMessage]:
        """사용자 메시지를 저장소와 메모리에 동시에 반영한다."""

        normalized = self._normalize_message(message=message)
        session = self._repository.ensure_session(session_id=session_id, title=title)
        self._ensure_memory_loaded(session_id=session.session_id)
        user_message = self._repository.append_message(
            session_id=session.session_id,
            role=ChatRole.USER,
            content=normalized,
        )
        self._memory_store.rpush(session_id=session.session_id, message=user_message)
        return session, user_message

    def append_assistant_message(self, session_id: str, content: str) -> ChatMessage:
        """어시스턴트 메시지를 저장소와 메모리에 동시에 반영한다."""

        normalized = self._normalize_message(message=content)
        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(
                code="CHAT_SESSION_NOT_FOUND",
                cause=f"session_id={session_id}",
            )
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        self._ensure_memory_loaded(session_id=session.session_id)
        assistant_message = self._repository.append_message(
            session_id=session.session_id,
            role=ChatRole.ASSISTANT,
            content=normalized,
        )
        self._memory_store.rpush(session_id=session.session_id, message=assistant_message)
        return assistant_message

    def process_enqueued_turn(
        self,
        session_id: str,
        user_message_id: str,
        user_message_content: str,
        user_sequence: int | None,
        context_window: int,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> ChatMessage:
        """큐에 등록된 사용자 입력 기준으로 어시스턴트 응답을 생성한다."""

        session = self._repository.get_session(session_id)
        if session is None:
            detail = ExceptionDetail(
                code="CHAT_SESSION_NOT_FOUND",
                cause=f"session_id={session_id}",
            )
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        self._ensure_memory_loaded(session_id=session.session_id)
        history = self._build_context_history(
            session_id=session.session_id,
            context_window=context_window,
            exclude_message_id=user_message_id,
            max_sequence=(user_sequence - 1) if user_sequence is not None else None,
        )
        assistant_content = self._stream_or_invoke(
            session_id=session.session_id,
            user_message=user_message_content,
            history=history,
            on_chunk=on_chunk,
        )
        assistant_message = self.append_assistant_message(
            session_id=session.session_id,
            content=assistant_content,
        )
        return assistant_message

    def _build_turn_result(
        self,
        session: ChatSession,
        user_message: ChatMessage,
        assistant_message: ChatMessage,
    ) -> ChatTurnResult:
        """턴 처리 결과 모델을 생성한다."""

        latest_session = self._repository.get_session(session.session_id)
        if latest_session is None:
            latest_session = session
        self._logger.info("Chat 턴 처리 완료")
        return ChatTurnResult(
            session=latest_session,
            user_message=user_message,
            assistant_message=assistant_message,
        )

    def _build_context_history(
        self,
        session_id: str,
        context_window: int,
        exclude_message_id: Optional[str] = None,
        max_sequence: Optional[int] = None,
    ) -> list[ChatMessage]:
        """메모리 저장소에서 컨텍스트 이력을 구성한다."""

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

    def _stream_or_invoke(
        self,
        session_id: str,
        user_message: str,
        history: list[ChatMessage],
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        """스트리밍을 우선 시도하고 비어 있으면 invoke로 보완한다."""

        chunks: list[str] = []
        for chunk in self._graph.stream(
            session_id=session_id,
            user_message=user_message,
            history=history,
        ):
            if not chunk:
                continue
            chunks.append(chunk)
            if on_chunk is not None:
                on_chunk(chunk)
        content = "".join(chunks).strip()
        if content:
            return content
        invoked = self._graph.invoke(
            session_id=session_id,
            user_message=user_message,
            history=history,
        )
        return invoked.strip()

    def _ensure_memory_loaded(self, session_id: str) -> None:
        """세션 메모리가 비어 있으면 저장소에서 로드한다."""

        self._memory_store.ensure_session(
            session_id=session_id,
            loader=lambda: self._repository.get_recent_messages(
                session_id=session_id,
                limit=self._memory_store.max_messages,
            ),
        )

    def _normalize_message(self, message: str) -> str:
        """메시지를 정규화하고 유효성을 검증한다."""

        if not message or not message.strip():
            detail = ExceptionDetail(code="CHAT_MESSAGE_EMPTY", cause="message is empty")
            raise BaseAppException("메시지는 비어 있을 수 없습니다.", detail)
        return message.strip()
