"""
목적: Chat API 서비스 레이어를 제공한다.
설명: 세션 생성/조회/삭제와 queue-task 흐름을 Chat 런타임에 연결한다.
디자인 패턴: 서비스 레이어
참조: src/base_template/api/chat/services/chat_runtime.py, src/base_template/api/chat/models
"""

from __future__ import annotations

import json
from typing import Iterator
from typing import Optional

from base_template.api.chat.models import (
    CreateSessionRequest,
    CreateSessionResponse,
    MessageListResponse,
    MessageResponse,
    QueueMessageRequest,
    QueueMessageResponse,
    TaskResultResponse,
    TaskStatusResponse,
    SessionListResponse,
    SessionSummaryResponse,
    StreamEventType,
    StreamPayload,
)
from base_template.core.chat.models import ChatMessage, ChatSession
from base_template.api.chat.services.chat_runtime import ChatRuntime
from base_template.api.chat.services.task_manager import ChatTaskManager
from base_template.shared.logging import Logger, create_default_logger


class ChatAPIService:
    """Chat API 전용 서비스."""

    def __init__(
        self,
        runtime: Optional[ChatRuntime] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._logger = logger or create_default_logger("ChatAPIService")
        self._runtime = runtime or ChatRuntime(logger=self._logger)
        self._task_manager = ChatTaskManager(
            runtime=self._runtime,
            logger=self._logger,
        )

    def close(self) -> None:
        """내부 리소스를 정리한다."""

        self._task_manager.close()
        self._runtime.close()

    def create_session(self, request: CreateSessionRequest) -> CreateSessionResponse:
        """세션 생성 요청을 처리한다."""

        session = self._runtime.create_session(
            title=request.title,
        )
        return CreateSessionResponse(session_id=session.session_id)

    def list_sessions(self, limit: int, offset: int) -> SessionListResponse:
        """세션 목록 조회 요청을 처리한다."""

        sessions = self._runtime.list_sessions(limit=limit, offset=offset)
        return SessionListResponse(
            sessions=[self._to_session_summary(item) for item in sessions],
            limit=limit,
            offset=offset,
        )

    def list_messages(self, session_id: str, limit: int, offset: int) -> MessageListResponse:
        """메시지 목록 조회 요청을 처리한다."""

        messages = self._runtime.list_messages(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        return MessageListResponse(
            session_id=session_id,
            messages=[self._to_message(item) for item in messages],
            limit=limit,
            offset=offset,
        )

    def delete_session(self, session_id: str) -> None:
        """세션 삭제 요청을 처리한다."""

        self._runtime.delete_session(session_id=session_id)

    def enqueue_message(
        self,
        session_id: str,
        request: QueueMessageRequest,
    ) -> QueueMessageResponse:
        """세션 메시지 큐 등록 요청을 처리한다."""

        task_id, queued_at = self._task_manager.enqueue(
            session_id=session_id,
            message=request.message,
            context_window=request.context_window,
        )
        return QueueMessageResponse(
            session_id=session_id,
            task_id=task_id,
            queued_at=queued_at,
        )

    def get_task_status(self, session_id: str, task_id: str) -> TaskStatusResponse:
        """태스크 상태 조회를 처리한다."""

        return self._task_manager.get_status(session_id=session_id, task_id=task_id)

    def get_task_result(self, session_id: str, task_id: str) -> TaskResultResponse:
        """태스크 결과 조회를 처리한다."""

        return self._task_manager.get_result(session_id=session_id, task_id=task_id)

    def iter_task_stream_events(self, session_id: str, task_id: str) -> Iterator[str]:
        """SSE 이벤트 스트림을 생성한다."""

        yield self._build_sse(
            "message",
            StreamPayload(
                session_id=session_id,
                task_id=task_id,
                type=StreamEventType.START,
                content="",
            ).model_dump(mode="json"),
        )
        for chunk in self._task_manager.iter_stream_chunks(session_id=session_id, task_id=task_id):
            payload = StreamPayload(
                session_id=session_id,
                task_id=task_id,
                type=StreamEventType.TOKEN,
                content=chunk,
            )
            yield self._build_sse("message", payload.model_dump(mode="json"))
        result = self.get_task_result(session_id=session_id, task_id=task_id)
        final_content = None
        if (
            result.assistant_message is not None
            and isinstance(result.assistant_message.content, str)
            and result.assistant_message.content.strip()
        ):
            final_content = result.assistant_message.content
        if result.status.value == "FAILED":
            yield self._build_sse(
                "message",
                StreamPayload(
                    session_id=session_id,
                    task_id=task_id,
                    type=StreamEventType.ERROR,
                    content="",
                    error_message=result.error_message,
                    status=result.status.value,
                ).model_dump(mode="json"),
            )
        yield self._build_sse(
            "message",
            StreamPayload(
                session_id=session_id,
                task_id=task_id,
                type=StreamEventType.DONE,
                content="",
                status=result.status.value,
                error_message=result.error_message,
                final_content=final_content,
                assistant_message=result.assistant_message,
            ).model_dump(mode="json"),
        )

    def _to_message(self, message: ChatMessage) -> MessageResponse:
        return MessageResponse(
            message_id=message.message_id,
            role=message.role,
            content=message.content,
            sequence=message.sequence,
            created_at=message.created_at,
        )

    def _to_session_summary(self, session: ChatSession) -> SessionSummaryResponse:
        return SessionSummaryResponse(
            session_id=session.session_id,
            title=session.title,
            updated_at=session.updated_at,
            message_count=session.message_count,
            last_message_preview=session.last_message_preview,
        )

    def _build_sse(self, event: str, payload: dict) -> str:
        body = json.dumps(payload, ensure_ascii=True)
        return f"event: {event}\ndata: {body}\n\n"
