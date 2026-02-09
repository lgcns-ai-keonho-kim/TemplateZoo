"""
목적: Chat 비동기 태스크 매니저를 제공한다.
설명: In-Memory Queue + Worker + ThreadPool 조합으로 task_id 기반 대화 처리를 수행한다.
디자인 패턴: 큐 기반 비동기 오케스트레이션
참조: src/base_template/api/chat/services/chat_runtime.py, src/base_template/shared/runtime
"""

from __future__ import annotations

import os
import queue as queue_module
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import uuid4

from base_template.api.chat.models import (
    MessageResponse,
    TaskResultResponse,
    TaskStatus,
    TaskStatusResponse,
)
from base_template.api.chat.services.chat_runtime import ChatRuntime
from base_template.core.chat.models import ChatMessage, utc_now
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger
from base_template.shared.runtime import (
    InMemoryQueue,
    QueueConfig,
    QueueItem,
    ThreadPool,
    ThreadPoolConfig,
    Worker,
    WorkerConfig,
)


def _read_env_int(name: str, default: int, minimum: int) -> int:
    """정수 환경 변수를 안전하게 읽는다."""

    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(minimum, value)


class _TaskStreamBuffer:
    """태스크 스트림 버퍼.

    Redis의 rpush/lpop 패턴과 유사하게 동작하며,
    max_chunks를 지정하면 생산자-소비자 간 백프레셔를 적용한다.
    """

    def __init__(self, max_chunks: int = 0) -> None:
        self._condition = threading.Condition()
        self._chunks: deque[str] = deque()
        self._closed = False
        self._max_chunks = max(0, max_chunks)

    def rpush(self, chunk: str) -> None:
        """스트림 우측에 청크를 추가한다."""

        with self._condition:
            while (
                not self._closed
                and self._max_chunks > 0
                and len(self._chunks) >= self._max_chunks
            ):
                self._condition.wait(timeout=0.2)
            if self._closed:
                return
            self._chunks.append(str(chunk))
            self._condition.notify_all()

    def lpop(self, timeout: float | None = 0.5) -> str | None:
        """스트림 좌측에서 청크를 꺼낸다."""

        with self._condition:
            if not self._chunks and not self._closed:
                self._condition.wait(timeout=timeout)
            if self._chunks:
                chunk = self._chunks.popleft()
                self._condition.notify_all()
                return chunk
            return None

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def is_closed(self) -> bool:
        with self._condition:
            return self._closed

    def iter_chunks(self) -> Iterator[str]:
        while True:
            chunk = self.lpop(timeout=0.5)
            if chunk is not None:
                yield chunk
                continue
            if self.is_closed():
                return


@dataclass
class _TaskRuntimeState:
    """태스크 런타임 상태."""

    session_id: str
    task_id: str
    user_message: str
    user_message_id: str
    user_sequence: int
    context_window: int
    created_at: datetime
    status: TaskStatus
    last_accessed_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    assistant_message: MessageResponse | None = None
    stream: _TaskStreamBuffer | None = None


class ChatTaskManager:
    """Chat 비동기 태스크 매니저."""

    def __init__(
        self,
        runtime: ChatRuntime,
        logger: Logger | None = None,
    ) -> None:
        self._runtime = runtime
        self._logger = logger or create_default_logger("ChatTaskManager")
        self._lock = threading.RLock()
        self._tasks: dict[str, _TaskRuntimeState] = {}
        self._session_locks: dict[str, threading.Lock] = {}

        default_workers = max(4, (os.cpu_count() or 1) * 4)
        max_workers = _read_env_int("CHAT_TASK_MAX_WORKERS", default_workers, 1)
        queue_max_size = _read_env_int("CHAT_TASK_QUEUE_MAX_SIZE", 1000, 0)
        self._stream_max_chunks = _read_env_int("CHAT_TASK_STREAM_MAX_CHUNKS", 4096, 0)
        self._task_result_ttl_seconds = _read_env_int("CHAT_TASK_RESULT_TTL_SECONDS", 1800, 60)
        self._task_max_stored = _read_env_int("CHAT_TASK_MAX_STORED", 10000, 100)
        self._task_cleanup_interval_seconds = _read_env_int(
            "CHAT_TASK_CLEANUP_INTERVAL_SECONDS",
            30,
            5,
        )
        self._last_cleanup_at = utc_now()

        worker_hint = os.getenv("UVICORN_WORKERS") or os.getenv("WEB_CONCURRENCY")
        if worker_hint:
            try:
                worker_count = int(worker_hint)
            except ValueError:
                worker_count = 1
            if worker_count > 1:
                self._logger.warning(
                    "In-Memory TaskManager는 멀티 프로세스 상태 공유를 지원하지 않습니다. "
                    "status/result/stream 일관성을 위해 단일 프로세스 또는 외부 저장소를 사용하세요."
                )

        self._queue = InMemoryQueue(
            config=QueueConfig(max_size=queue_max_size, default_timeout=0.2),
            logger=self._logger,
        )
        self._worker = Worker(
            queue=self._queue,
            config=WorkerConfig(
                name="ChatTaskWorker",
                poll_timeout=0.2,
                max_retries=0,
                stop_on_error=False,
            ),
            logger=self._logger,
        )
        self._thread_pool = ThreadPool(
            config=ThreadPoolConfig(
                max_workers=max_workers,
                thread_name_prefix="chat-task",
            ),
            logger=self._logger,
        )
        self._thread_pool.__enter__()

        @self._thread_pool.task
        def run_task(session_id: str, task_id: str) -> None:
            self._execute_task(session_id=session_id, task_id=task_id)

        self._run_task = run_task

        @self._worker
        def consume(item: QueueItem) -> None:
            payload = item.payload
            if not isinstance(payload, dict):
                return
            session_id = str(payload.get("session_id") or "")
            task_id = str(payload.get("task_id") or "")
            if not session_id or not task_id:
                return
            self._run_task(session_id, task_id)

        self._worker.start()

    def close(self) -> None:
        """리소스를 정리한다."""

        self._worker.stop()
        self._thread_pool.shutdown(wait=True)
        with self._lock:
            for state in self._tasks.values():
                if state.stream is not None:
                    state.stream.close()
            self._tasks.clear()
            self._session_locks.clear()

    def enqueue(self, session_id: str, message: str, context_window: int) -> tuple[str, datetime]:
        """메시지를 큐에 등록하고 task_id를 반환한다."""

        self._prune_tasks_if_needed()

        if not message or not message.strip():
            detail = ExceptionDetail(code="CHAT_MESSAGE_EMPTY", cause="message is empty")
            raise BaseAppException("메시지는 비어 있을 수 없습니다.", detail)

        session_lock = self._get_session_lock(session_id=session_id)
        with session_lock:
            session = self._runtime.get_session(session_id)
            if session is None:
                detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={session_id}")
                raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)

            _, user_message = self._runtime.append_user_message(
                message=message.strip(),
                session_id=session_id,
            )

            task_id = str(uuid4())
            created_at = utc_now()
            state = _TaskRuntimeState(
                session_id=session_id,
                task_id=task_id,
                user_message=user_message.content,
                user_message_id=user_message.message_id,
                user_sequence=user_message.sequence,
                context_window=max(context_window, 1),
                created_at=created_at,
                status=TaskStatus.QUEUED,
                last_accessed_at=created_at,
                stream=_TaskStreamBuffer(max_chunks=self._stream_max_chunks),
            )
            with self._lock:
                self._tasks[self._task_key(session_id, task_id)] = state

        try:
            self._queue.put({"session_id": session_id, "task_id": task_id})
        except queue_module.Full as error:
            with self._lock:
                self._tasks.pop(self._task_key(session_id, task_id), None)
            detail = ExceptionDetail(code="CHAT_QUEUE_FULL", cause=str(error))
            raise BaseAppException("대화 요청 큐가 가득 찼습니다. 잠시 후 다시 시도하세요.", detail, error) from error
        except Exception as error:  # noqa: BLE001
            with self._lock:
                self._tasks.pop(self._task_key(session_id, task_id), None)
            detail = ExceptionDetail(code="CHAT_QUEUE_ERROR", cause=str(error))
            raise BaseAppException("대화 요청 큐 등록에 실패했습니다.", detail, error) from error
        return task_id, created_at

    def get_status(self, session_id: str, task_id: str) -> TaskStatusResponse:
        """태스크 상태를 반환한다."""

        state = self._get_state(session_id, task_id)
        self._touch_state(state)
        self._prune_tasks_if_needed()
        return TaskStatusResponse(
            session_id=state.session_id,
            task_id=state.task_id,
            status=state.status,
            created_at=state.created_at,
            started_at=state.started_at,
            completed_at=state.completed_at,
            error_message=state.error_message,
        )

    def get_result(self, session_id: str, task_id: str) -> TaskResultResponse:
        """태스크 결과를 반환한다."""

        state = self._get_state(session_id, task_id)
        self._touch_state(state)
        self._prune_tasks_if_needed()
        return TaskResultResponse(
            session_id=state.session_id,
            task_id=state.task_id,
            status=state.status,
            assistant_message=state.assistant_message,
            error_message=state.error_message,
        )

    def iter_stream_chunks(self, session_id: str, task_id: str) -> Iterator[str]:
        """태스크 스트림 청크를 순차 반환한다."""

        state = self._get_state(session_id, task_id)
        self._touch_state(state)
        stream = state.stream
        if stream is None:
            return iter(())

        def generator() -> Iterator[str]:
            for chunk in stream.iter_chunks():
                self._touch_state(state)
                yield chunk
            self._touch_state(state)
            self._prune_tasks_if_needed()

        return generator()

    def _execute_task(self, session_id: str, task_id: str) -> None:
        state = self._get_state(session_id, task_id)
        self._set_status(state, TaskStatus.RUNNING, started_at=utc_now())
        session_lock = self._get_session_lock(session_id=state.session_id)
        try:
            streamed = False

            def on_chunk(chunk: str) -> None:
                nonlocal streamed
                if not chunk:
                    return
                if state.stream is not None:
                    state.stream.rpush(chunk)
                if not streamed:
                    streamed = True
                    self._set_status(state, TaskStatus.STREAMING)

            # 워커 스레드에서는 별도 런타임을 생성해 SQLite 스레드 제약을 회피한다.
            thread_runtime = ChatRuntime(
                logger=self._logger,
                memory_store=self._runtime.memory_store,
            )
            try:
                with session_lock:
                    assistant_message = thread_runtime.process_enqueued_turn(
                        session_id=state.session_id,
                        user_message_id=state.user_message_id,
                        user_message_content=state.user_message,
                        user_sequence=state.user_sequence,
                        context_window=state.context_window,
                        on_chunk=on_chunk,
                    )
            finally:
                thread_runtime.close()
            if not streamed and assistant_message.content and state.stream is not None:
                self._set_status(state, TaskStatus.STREAMING)
                state.stream.rpush(assistant_message.content)
            state.assistant_message = self._to_message_response(assistant_message)
            self._set_status(state, TaskStatus.COMPLETED, completed_at=utc_now())
        except BaseAppException as error:
            state.error_message = self._format_base_error_message(error)
            self._set_status(state, TaskStatus.FAILED, completed_at=utc_now())
        except Exception as error:  # noqa: BLE001
            state.error_message = str(error)
            self._set_status(state, TaskStatus.FAILED, completed_at=utc_now())
        finally:
            if state.stream is not None:
                state.stream.close()
            self._touch_state(state)
            self._prune_tasks_if_needed()

    def _to_message_response(self, message: ChatMessage) -> MessageResponse:
        return MessageResponse(
            message_id=message.message_id,
            role=message.role,
            content=message.content,
            sequence=message.sequence,
            created_at=message.created_at,
        )

    def _format_base_error_message(self, error: BaseAppException) -> str:
        """도메인 예외를 UI 노출용 단일 문자열로 변환한다."""

        cause = str(error.detail.cause or "").strip()
        if not cause:
            return error.message
        return f"{error.message} (cause={cause})"

    def _set_status(
        self,
        state: _TaskRuntimeState,
        status: TaskStatus,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        with self._lock:
            state.status = status
            if started_at is not None:
                state.started_at = started_at
            if completed_at is not None:
                state.completed_at = completed_at
            state.last_accessed_at = utc_now()

    def _touch_state(self, state: _TaskRuntimeState) -> None:
        with self._lock:
            state.last_accessed_at = utc_now()

    def _get_state(self, session_id: str, task_id: str) -> _TaskRuntimeState:
        key = self._task_key(session_id, task_id)
        with self._lock:
            state = self._tasks.get(key)
        if state is None:
            detail = ExceptionDetail(
                code="CHAT_TASK_NOT_FOUND",
                cause=f"session_id={session_id}, task_id={task_id}",
            )
            raise BaseAppException("요청한 태스크를 찾을 수 없습니다.", detail)
        return state

    def _task_key(self, session_id: str, task_id: str) -> str:
        return f"{session_id}:{task_id}"

    def _get_session_lock(self, session_id: str) -> threading.Lock:
        with self._lock:
            session_lock = self._session_locks.get(session_id)
            if session_lock is None:
                session_lock = threading.Lock()
                self._session_locks[session_id] = session_lock
        return session_lock

    def _prune_tasks_if_needed(self, force: bool = False) -> None:
        now = utc_now()
        with self._lock:
            elapsed = (now - self._last_cleanup_at).total_seconds()
            if not force and elapsed < self._task_cleanup_interval_seconds:
                return
            self._last_cleanup_at = now

            removable: list[str] = []
            for key, state in self._tasks.items():
                if state.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
                    continue
                age_seconds = (now - state.last_accessed_at).total_seconds()
                if age_seconds >= self._task_result_ttl_seconds:
                    removable.append(key)

            for key in removable:
                stale = self._tasks.pop(key, None)
                if stale is not None and stale.stream is not None:
                    stale.stream.close()

            overflow = len(self._tasks) - self._task_max_stored
            if overflow > 0:
                terminal = [
                    (state.last_accessed_at, key)
                    for key, state in self._tasks.items()
                    if state.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}
                ]
                terminal.sort(key=lambda item: item[0])
                for _, key in terminal[:overflow]:
                    dropped = self._tasks.pop(key, None)
                    if dropped is not None and dropped.stream is not None:
                        dropped.stream.close()

            active_sessions = {
                state.session_id
                for state in self._tasks.values()
                if state.status in {TaskStatus.QUEUED, TaskStatus.RUNNING, TaskStatus.STREAMING}
            }
            for session_id in list(self._session_locks):
                session_lock = self._session_locks.get(session_id)
                if session_id in active_sessions:
                    continue
                if session_lock is None:
                    continue
                if session_lock.locked():
                    continue
                self._session_locks.pop(session_id, None)
