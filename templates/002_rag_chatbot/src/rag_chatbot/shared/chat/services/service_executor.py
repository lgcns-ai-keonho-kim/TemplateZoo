"""
목적: Chat 실행 오케스트레이션을 제공한다.
설명: JobQueue 소비 워커와 EventBuffer 기반 SSE 중계를 관리한다.
디자인 패턴: 실행 코디네이터
참조: src/rag_chatbot/shared/chat/interface/ports.py
"""

from __future__ import annotations

import asyncio
import json
import queue as queue_module
import threading
import time
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from rag_chatbot.shared.chat.interface import ChatServicePort, ServiceExecutorPort
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger
from rag_chatbot.shared.runtime.buffer import StreamEventItem
from rag_chatbot.shared.runtime.queue import QueueItem


class ServiceExecutor(ServiceExecutorPort):
    """Chat 실행 오케스트레이터."""

    _EVENT_START = "start"
    _EVENT_TOKEN = "token"
    _EVENT_REFERENCES = "references"
    _EVENT_DONE = "done"
    _EVENT_ERROR = "error"
    _ALLOWED_EVENT_TYPES = {
        _EVENT_START,
        _EVENT_TOKEN,
        _EVENT_REFERENCES,
        _EVENT_DONE,
        _EVENT_ERROR,
    }
    _PERSIST_STOP = "__persist_stop__"
    _STATUS_IDLE = "IDLE"
    _STATUS_QUEUED = "QUEUED"
    _STATUS_RUNNING = "RUNNING"
    _STATUS_COMPLETED = "COMPLETED"
    _STATUS_FAILED = "FAILED"
    _ALLOWED_STATUS = {
        _STATUS_IDLE,
        _STATUS_QUEUED,
        _STATUS_RUNNING,
        _STATUS_COMPLETED,
        _STATUS_FAILED,
    }

    def __init__(
        self,
        service: ChatServicePort,
        job_queue: Any,
        event_buffer: Any,
        llm_logger: Logger | None = None,
        service_logger: Logger | None = None,
        timeout_seconds: float = 180.0,
        persist_retry_limit: int = 2,
        persist_retry_delay_seconds: float = 0.5,
    ) -> None:
        self._service = service
        self._job_queue = job_queue
        self._event_buffer = event_buffer
        self._llm_logger = llm_logger or create_default_logger("ChatExecutorLLM")
        self._service_logger = service_logger or create_default_logger("ChatExecutor")
        self._timeout_seconds = max(1.0, float(timeout_seconds))
        self._lock = threading.RLock()
        self._session_locks: dict[str, threading.Lock] = {}
        self._session_statuses: dict[str, str] = {}
        self._job_poll_timeout = self._resolve_job_poll_timeout()
        self._event_poll_timeout = self._resolve_event_poll_timeout()
        self._persist_retry_limit = max(0, int(persist_retry_limit))
        self._persist_retry_delay_seconds = max(0.01, float(persist_retry_delay_seconds))
        self._persist_queue: queue_module.Queue = queue_module.Queue()
        self._persist_stop_event = threading.Event()
        self._worker_stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._persist_thread = threading.Thread(target=self._persist_loop, daemon=True)
        self._worker_thread.start()
        self._persist_thread.start()

    def submit_job(
        self,
        session_id: str | None,
        user_query: str,
        context_window: int,
    ) -> dict[str, str]:
        """작업 큐에 채팅 실행 요청을 적재한다."""

        resolved_session_id = self._resolve_session_id(session_id=session_id)
        request_id = str(uuid4())
        payload = {
            "kind": "job",
            "value": {
                "session_id": resolved_session_id,
                "request_id": request_id,
                "user_query": user_query,
                "context_window": int(context_window),
            },
        }
        try:
            self._job_queue.put(payload, timeout=self._job_poll_timeout)
        except Exception as error:  # noqa: BLE001 - 큐 백엔드 예외를 도메인 예외로 래핑
            detail = ExceptionDetail(code="CHAT_JOB_QUEUE_FAILED", cause=str(error))
            raise BaseAppException("작업 큐에 요청을 저장하지 못했습니다.", detail) from error
        self._service_logger.info(
            f"chat.exec.queued: session_id={resolved_session_id}, request_id={request_id}"
        )
        self._set_session_status(session_id=resolved_session_id, status=self._STATUS_QUEUED)
        return {
            "session_id": resolved_session_id,
            "request_id": request_id,
            "status": "QUEUED",
        }

    def get_session_status(self, session_id: str) -> str | None:
        """세션의 최근 실행 상태를 반환한다."""

        candidate = str(session_id or "").strip()
        if not candidate:
            return None
        with self._lock:
            return self._session_statuses.get(candidate)

    def stream_events(self, session_id: str, request_id: str) -> Iterator[str]:
        """요청 단위 SSE 스트림을 생성한다."""

        idle_started_at = time.monotonic()
        try:
            while True:
                item = self._event_buffer.pop(
                    session_id=session_id,
                    request_id=request_id,
                    timeout=self._event_poll_timeout,
                )
                if item is None:
                    elapsed = time.monotonic() - idle_started_at
                    if elapsed <= self._timeout_seconds:
                        continue
                    timeout_payload = self._build_error_payload(
                        session_id=session_id,
                        request_id=request_id,
                        node="executor",
                        error_message="이벤트 스트림 대기 시간이 초과되었습니다.",
                    )
                    self._set_session_status(session_id=session_id, status=self._STATUS_FAILED)
                    yield self._build_sse("message", timeout_payload)
                    return

                idle_started_at = time.monotonic()
                try:
                    payload = self._build_public_payload(session_id=session_id, item=item)
                except ValueError as error:
                    self._service_logger.error(
                        f"chat.exec.protocol_error: session_id={session_id}, request_id={request_id}, error={error}"
                    )
                    failure = self._build_error_payload(
                        session_id=session_id,
                        request_id=request_id,
                        node="executor",
                        error_message=f"프로토콜 오류: {error}",
                    )
                    yield self._build_sse("message", failure)
                    return

                yield self._build_sse("message", payload)
                event_type = str(payload.get("type") or "")
                if event_type in {self._EVENT_DONE, self._EVENT_ERROR}:
                    return
        finally:
            self._event_buffer.cleanup(session_id=session_id, request_id=request_id)

    def shutdown(self) -> None:
        """실행기 워커를 안전하게 종료한다."""

        self._worker_stop_event.set()
        self._persist_stop_event.set()
        self._persist_queue.put({"kind": self._PERSIST_STOP})
        self._worker_thread.join(timeout=1.0)
        self._persist_thread.join(timeout=1.0)

    def _worker_loop(self) -> None:
        while not self._worker_stop_event.is_set():
            try:
                item = self._job_queue.get(timeout=self._job_poll_timeout)
            except Exception as error:  # noqa: BLE001 - 워커 루프 보호
                self._service_logger.error(f"chat.exec.queue_error: error={error}")
                time.sleep(self._job_poll_timeout)
                continue
            if item is None:
                continue
            job = self._extract_job_payload(item)
            if job is None:
                continue
            try:
                self._handle_job(job)
            except Exception as error:  # noqa: BLE001 - 워커 루프 보호
                self._service_logger.error(f"chat.exec.worker_error: error={error}")

    def _handle_job(self, job: dict[str, Any]) -> None:
        session_id = str(job.get("session_id") or "").strip()
        request_id = str(job.get("request_id") or "").strip()
        user_query = str(job.get("user_query") or "")
        context_window = int(job.get("context_window") or 20)
        if not session_id or not request_id:
            self._service_logger.error(
                f"chat.exec.drop: invalid job payload session_id={session_id}, request_id={request_id}"
            )
            return

        started_at = time.monotonic()
        token_count = 0
        done_emitted = False
        done_content = ""
        done_node = "response"
        done_metadata: dict[str, Any] | None = None
        self._set_session_status(session_id=session_id, status=self._STATUS_RUNNING)
        self._emit_event(
            session_id=session_id,
            request_id=request_id,
            event_type=self._EVENT_START,
            node="executor",
            data="",
        )
        session_lock = self._get_session_lock(session_id=session_id)

        try:
            with session_lock:
                consumed = asyncio.run(
                    self._consume_service_astream(
                        session_id=session_id,
                        request_id=request_id,
                        user_query=user_query,
                        context_window=context_window,
                        started_at=started_at,
                    )
                )
                token_count = int(consumed.get("token_count") or 0)
                done_emitted = bool(consumed.get("done_emitted") is True)
                done_content = str(consumed.get("done_content") or "")
                done_node = str(consumed.get("done_node") or "response")
                raw_done_metadata = consumed.get("done_metadata")
                if isinstance(raw_done_metadata, dict):
                    done_metadata = raw_done_metadata
        except BaseAppException as error:
            message = self._format_base_error_message(error)
            self._service_logger.error(
                f"chat.exec.error: session_id={session_id}, request_id={request_id}, code={error.detail.code}"
            )
            self._set_session_status(session_id=session_id, status=self._STATUS_FAILED)
            self._emit_event(
                session_id=session_id,
                request_id=request_id,
                event_type=self._EVENT_ERROR,
                node="executor",
                data=message,
                metadata={"error_code": error.detail.code},
            )
            return
        except TimeoutError as error:
            self._service_logger.error(
                f"chat.exec.timeout: session_id={session_id}, request_id={request_id}"
            )
            self._set_session_status(session_id=session_id, status=self._STATUS_FAILED)
            self._emit_event(
                session_id=session_id,
                request_id=request_id,
                event_type=self._EVENT_ERROR,
                node="executor",
                data=str(error),
            )
            return
        except Exception as error:  # noqa: BLE001 - 워커 루프 보호
            self._service_logger.error(
                f"chat.exec.error: session_id={session_id}, request_id={request_id}, error={error}"
            )
            self._set_session_status(session_id=session_id, status=self._STATUS_FAILED)
            self._emit_event(
                session_id=session_id,
                request_id=request_id,
                event_type=self._EVENT_ERROR,
                node="executor",
                data=str(error),
            )
            return

        if not done_emitted:
            self._service_logger.error(
                f"chat.exec.error: session_id={session_id}, request_id={request_id}, cause=done_missing"
            )
            self._set_session_status(session_id=session_id, status=self._STATUS_FAILED)
            self._emit_event(
                session_id=session_id,
                request_id=request_id,
                event_type=self._EVENT_ERROR,
                node="executor",
                data="스트림 완료 이벤트를 생성하지 못했습니다.",
            )
            return

        self._enqueue_persist_task(
            session_id=session_id,
            request_id=request_id,
            content=done_content,
            node=done_node,
            metadata=done_metadata,
        )
        elapsed = time.monotonic() - started_at
        self._llm_logger.info(
            f"chat.exec.llm: session_id={session_id}, request_id={request_id}, elapsed_ms={int(elapsed * 1000)}, token_count={token_count}"
        )

    async def _consume_service_astream(
        self,
        *,
        session_id: str,
        request_id: str,
        user_query: str,
        context_window: int,
        started_at: float,
    ) -> dict[str, Any]:
        """서비스 비동기 스트림을 소비하고 실행 요약을 반환한다."""

        token_count = 0
        done_emitted = False
        done_content = ""
        done_node = "response"
        done_metadata: dict[str, Any] | None = None

        async for event in self._service.astream(
            session_id=session_id,
            user_query=user_query,
            context_window=context_window,
        ):
            self._raise_timeout_if_needed(started_at=started_at)
            normalized = self._normalize_graph_event(event=event)
            if normalized is None:
                continue

            event_type = normalized["event"]
            if event_type == self._EVENT_TOKEN:
                token_count += 1
            if event_type == self._EVENT_DONE:
                done_emitted = True
                metadata = normalized.get("metadata")
                merged_metadata = self._merge_metadata(
                    metadata=metadata,
                    patch={"token_count": token_count},
                )
                normalized["metadata"] = merged_metadata
                done_content = str(normalized.get("data") or "")
                done_node = str(normalized.get("node") or "response")
                done_metadata = merged_metadata
                self._set_session_status(session_id=session_id, status=self._STATUS_COMPLETED)
            if event_type == self._EVENT_ERROR:
                self._set_session_status(session_id=session_id, status=self._STATUS_FAILED)

            self._emit_event(
                session_id=session_id,
                request_id=request_id,
                event_type=event_type,
                node=normalized["node"],
                data=normalized.get("data"),
                metadata=normalized.get("metadata"),
            )

            if event_type in {self._EVENT_DONE, self._EVENT_ERROR}:
                break

        return {
            "token_count": token_count,
            "done_emitted": done_emitted,
            "done_content": done_content,
            "done_node": done_node,
            "done_metadata": done_metadata,
        }

    def _persist_loop(self) -> None:
        while not self._persist_stop_event.is_set():
            try:
                task = self._persist_queue.get(timeout=self._job_poll_timeout)
            except queue_module.Empty:
                continue
            if not isinstance(task, dict):
                continue
            if str(task.get("kind") or "") == self._PERSIST_STOP:
                return
            try:
                self._process_persist_task(task)
            except Exception as error:  # noqa: BLE001 - 후처리 루프 보호
                self._service_logger.error(f"chat.persist.worker_error: error={error}")

    def _enqueue_persist_task(
        self,
        *,
        session_id: str,
        request_id: str,
        content: str,
        node: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        if not str(content or "").strip():
            self._service_logger.warning(
                f"chat.persist.skip: session_id={session_id}, request_id={request_id}, reason=empty_content"
            )
            return
        task = {
            "kind": "persist",
            "attempt": 0,
            "session_id": session_id,
            "request_id": request_id,
            "node": node,
            "content": content,
            "metadata": metadata,
        }
        self._persist_queue.put(task)

    def _process_persist_task(self, task: dict[str, Any]) -> None:
        session_id = str(task.get("session_id") or "").strip()
        request_id = str(task.get("request_id") or "").strip()
        node = str(task.get("node") or "response")
        content = str(task.get("content") or "")
        attempt = int(task.get("attempt") or 0)
        metadata = task.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            metadata = None
        if not session_id or not request_id:
            self._service_logger.error(
                f"chat.persist.drop: invalid task session_id={session_id}, request_id={request_id}"
            )
            return

        persist_metadata = self._merge_metadata(
            metadata=metadata,
            patch={"request_id": request_id, "node": node},
        )
        try:
            persisted = self._service.persist_assistant_message(
                session_id=session_id,
                request_id=request_id,
                content=content,
                metadata=persist_metadata,
            )
            if persisted:
                self._service_logger.info(
                    f"chat.persist.saved: session_id={session_id}, request_id={request_id}"
                )
            else:
                self._service_logger.info(
                    f"chat.persist.skipped: session_id={session_id}, request_id={request_id}"
                )
        except BaseAppException as error:
            self._retry_persist_task(
                task=task,
                attempt=attempt,
                reason=f"{error.detail.code}:{error.detail.cause}",
            )
        except Exception as error:  # noqa: BLE001 - 후처리 루프 보호
            self._retry_persist_task(task=task, attempt=attempt, reason=str(error))

    def _retry_persist_task(self, task: dict[str, Any], attempt: int, reason: str) -> None:
        next_attempt = attempt + 1
        session_id = str(task.get("session_id") or "").strip()
        request_id = str(task.get("request_id") or "").strip()
        if next_attempt > self._persist_retry_limit:
            self._service_logger.error(
                f"chat.persist.failed: session_id={session_id}, request_id={request_id}, reason={reason}"
            )
            return
        task["attempt"] = next_attempt
        self._service_logger.warning(
            f"chat.persist.retry: session_id={session_id}, request_id={request_id}, attempt={next_attempt}, reason={reason}"
        )
        time.sleep(self._persist_retry_delay_seconds)
        self._persist_queue.put(task)

    def _resolve_session_id(self, session_id: str | None) -> str:
        candidate = str(session_id or "").strip()
        if not candidate:
            session = self._service.create_session()
            return str(session.session_id)
        existing = self._service.get_session(candidate)
        if existing is None:
            detail = ExceptionDetail(code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={candidate}")
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        return candidate

    def _normalize_graph_event(self, event: Any) -> dict[str, Any] | None:
        if not isinstance(event, dict):
            return None
        node = str(event.get("node") or "").strip()
        event_name = str(event.get("event") or "").strip()
        data = event.get("data")
        metadata = event.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            metadata = None

        if event_name == "token":
            content = str(data or "")
            if not content:
                return None
            return {
                "event": self._EVENT_TOKEN,
                "node": node or "response",
                "data": content,
                "metadata": metadata,
            }

        if event_name == "assistant_message":
            if node != "blocked":
                return None
            content = str(data or "")
            if not content:
                return None
            return {
                "event": self._EVENT_TOKEN,
                "node": "blocked",
                "data": content,
                "metadata": metadata,
            }

        if event_name == "references":
            payload = data if isinstance(data, list) else []
            return {
                "event": self._EVENT_REFERENCES,
                "node": node or "rag",
                "data": payload,
                "metadata": metadata,
            }

        if event_name == "done":
            return {
                "event": self._EVENT_DONE,
                "node": node or "response",
                "data": str(data or ""),
                "metadata": metadata,
            }

        if event_name == "error":
            return {
                "event": self._EVENT_ERROR,
                "node": node or "executor",
                "data": str(data or ""),
                "metadata": metadata,
            }

        return None

    def _emit_event(
        self,
        *,
        session_id: str,
        request_id: str,
        event_type: str,
        node: str,
        data: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            self._event_buffer.push(
                session_id=session_id,
                request_id=request_id,
                event={
                    "event": event_type,
                    "data": data,
                    "node": node,
                    "request_id": request_id,
                    "metadata": metadata,
                },
            )
        except Exception as error:  # noqa: BLE001 - 워커 중단 방지
            self._service_logger.error(
                f"chat.exec.buffer_error: session_id={session_id}, request_id={request_id}, error={error}"
            )

    def _build_sse(self, event: str, payload: dict[str, Any]) -> str:
        body = json.dumps(payload, ensure_ascii=True)
        return f"event: {event}\ndata: {body}\n\n"

    def _build_public_payload(self, session_id: str, item: StreamEventItem) -> dict[str, Any]:
        event_type = str(item.event or "").strip()
        request_id = str(item.request_id or "").strip()
        node = str(item.node or "").strip()
        if event_type not in self._ALLOWED_EVENT_TYPES:
            raise ValueError(f"지원하지 않는 event 타입입니다: {event_type}")
        if not request_id:
            raise ValueError("request_id 필드가 비어 있습니다.")
        if not node:
            raise ValueError("node 필드가 비어 있습니다.")

        content = self._to_content_text(item.data)
        payload: dict[str, Any] = {
            "session_id": session_id,
            "request_id": request_id,
            "type": event_type,
            "node": node,
            "content": content,
            "status": None,
            "error_message": None,
        }
        if item.metadata is not None:
            payload["metadata"] = item.metadata

        if event_type == self._EVENT_DONE:
            payload["status"] = "COMPLETED"
        if event_type == self._EVENT_ERROR:
            payload["status"] = "FAILED"
            payload["error_message"] = content or "응답 생성에 실패했습니다."
        return payload

    def _build_error_payload(
        self,
        *,
        session_id: str,
        request_id: str,
        node: str,
        error_message: str,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "request_id": request_id,
            "type": self._EVENT_ERROR,
            "node": node,
            "content": "",
            "status": "FAILED",
            "error_message": error_message,
        }

    def _extract_job_payload(self, item: Any) -> dict[str, Any] | None:
        payload: Any
        if isinstance(item, QueueItem):
            payload = item.payload
        else:
            payload = item
        if not isinstance(payload, dict):
            return None
        if str(payload.get("kind") or "").strip() != "job":
            return None
        value = payload.get("value")
        if not isinstance(value, dict):
            return None
        return value

    def _merge_metadata(
        self,
        *,
        metadata: dict[str, Any] | None,
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        if metadata is not None:
            merged.update(metadata)
        merged.update(patch)
        return merged

    def _get_session_lock(self, session_id: str) -> threading.Lock:
        with self._lock:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = threading.Lock()
                self._session_locks[session_id] = lock
            return lock

    def _set_session_status(self, *, session_id: str, status: str) -> None:
        """세션 실행 상태를 갱신한다."""

        candidate = str(session_id or "").strip()
        normalized = str(status or "").strip().upper()
        if not candidate:
            return
        if normalized not in self._ALLOWED_STATUS:
            return
        with self._lock:
            current = self._session_statuses.get(candidate)
            # 실행 중(RUNNING) 상태를 큐 등록(QUEUED)으로 역전시키지 않는다.
            if current == self._STATUS_RUNNING and normalized == self._STATUS_QUEUED:
                return
            self._session_statuses[candidate] = normalized

    def _raise_timeout_if_needed(self, started_at: float) -> None:
        elapsed = time.monotonic() - started_at
        if elapsed <= self._timeout_seconds:
            return
        detail = ExceptionDetail(
            code="CHAT_STREAM_TIMEOUT",
            cause=f"elapsed={elapsed:.3f}s, timeout={self._timeout_seconds:.3f}s",
        )
        raise BaseAppException("스트리밍 응답이 시간 제한을 초과했습니다.", detail)

    def _format_base_error_message(self, error: BaseAppException) -> str:
        cause = str(error.detail.cause or "").strip()
        if not cause:
            return error.message
        return f"{error.message} (cause={cause})"

    def _resolve_job_poll_timeout(self) -> float:
        config = getattr(self._job_queue, "config", None)
        if config is None:
            return 0.2
        timeout = getattr(config, "default_timeout", None)
        if timeout is None:
            return 0.2
        return max(float(timeout), 0.01)

    def _resolve_event_poll_timeout(self) -> float:
        config = getattr(self._event_buffer, "config", None)
        if config is None:
            return 0.2
        timeout = getattr(config, "default_timeout", None)
        if timeout is None:
            return 0.2
        return max(float(timeout), 0.01)

    def _to_content_text(self, data: Any) -> str:
        if data is None:
            return ""
        if isinstance(data, str):
            return data
        if isinstance(data, (int, float, bool)):
            return str(data)
        return json.dumps(data, ensure_ascii=False)
