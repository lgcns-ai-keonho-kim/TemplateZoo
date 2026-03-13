"""
목적: Chat 실행 오케스트레이션을 제공한다.
설명: JobQueue 소비 워커와 EventBuffer 기반 SSE 중계를 관리한다.
      그래프 내부 이벤트를 공개 이벤트(start/token/references/done/error)로 정규화한다.
디자인 패턴: 실행 코디네이터
참조: src/single_request_tool_agent/shared/agent/interface/ports.py
"""

from __future__ import annotations

import asyncio
import queue as queue_module
import threading
import time
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from single_request_tool_agent.shared.agent.services._service_executor_support import (
    _ServiceExecutorSupportMixin,
)
from single_request_tool_agent.shared.agent.interface import (
    ChatServicePort,
    ServiceExecutorPort,
)
from single_request_tool_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)
from single_request_tool_agent.shared.logging import Logger, create_default_logger


class ServiceExecutor(_ServiceExecutorSupportMixin, ServiceExecutorPort):
    """Chat 실행 오케스트레이터."""

    _EVENT_START = "start"
    _EVENT_TOKEN = "token"
    _EVENT_REFERENCES = "references"
    _EVENT_TOOL_START = "tool_start"
    _EVENT_TOOL_RESULT = "tool_result"
    _EVENT_TOOL_ERROR = "tool_error"
    _EVENT_DONE = "done"
    _EVENT_ERROR = "error"
    _ALLOWED_EVENT_TYPES = {
        _EVENT_START,
        _EVENT_TOKEN,
        _EVENT_REFERENCES,
        _EVENT_TOOL_START,
        _EVENT_TOOL_RESULT,
        _EVENT_TOOL_ERROR,
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
        self._persist_retry_delay_seconds = max(
            0.01, float(persist_retry_delay_seconds)
        )
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
            raise BaseAppException(
                "작업 큐에 요청을 저장하지 못했습니다.", detail
            ) from error
        self._service_logger.info(
            f"chat.exec.queued: session_id={resolved_session_id}, request_id={request_id}"
        )
        self._set_session_status(
            session_id=resolved_session_id, status=self._STATUS_QUEUED
        )
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
                    self._set_session_status(
                        session_id=session_id, status=self._STATUS_FAILED
                    )
                    yield self._build_sse("message", timeout_payload)
                    return

                idle_started_at = time.monotonic()
                try:
                    payload = self._build_public_payload(
                        session_id=session_id, item=item
                    )
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
                self._set_session_status(
                    session_id=session_id, status=self._STATUS_COMPLETED
                )
            if event_type == self._EVENT_ERROR:
                self._set_session_status(
                    session_id=session_id, status=self._STATUS_FAILED
                )

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
