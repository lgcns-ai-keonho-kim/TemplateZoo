"""
목적: Chat 실행 오케스트레이션을 제공한다.
설명: 단일 스트림 실행의 동시성/타임아웃/로깅과 SSE 이벤트 순서를 관리한다.
디자인 패턴: 실행 코디네이터
참조: src/base_template/shared/chat/contracts/ports.py
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from typing import Any

from base_template.shared.chat.interface import ChatServicePort, ServiceExecutorPort
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger
from base_template.shared.runtime.queue import QueueItem


class ServiceExecutor(ServiceExecutorPort):
    """Chat 실행 오케스트레이터."""

    def __init__(
        self,
        service: ChatServicePort,
        queue: Any,
        llm_logger: Logger | None = None,
        service_logger: Logger | None = None,
        timeout_seconds: float = 180.0,
    ) -> None:
        self._service = service
        self._queue = queue
        # NOTE: 실행 수명주기(start/done/error) 로그는 info 이상으로 기록한다.
        self._llm_logger = llm_logger or create_default_logger("ChatExecutorLLM")
        self._service_logger = service_logger or create_default_logger("ChatExecutor")
        self._timeout_seconds = max(1.0, float(timeout_seconds))
        self._lock = threading.RLock()
        self._queue_lock = threading.RLock()
        self._session_locks: dict[str, threading.Lock] = {}
        self._queue_poll_timeout = self._resolve_queue_timeout()

    def run_stream(
        self,
        session_id: str,
        user_query: str,
        context_window: int,
    ) -> Iterator[str]:
        """세션 단위 스트림 실행을 오케스트레이션한다."""

        session_lock = self._get_session_lock(session_id=session_id)

        def generator() -> Iterator[str]:
            started_at = time.monotonic()
            token_count = 0
            done_emitted = False
            producer_error: Exception | None = None
            producer_done = threading.Event()

            self._service_logger.info(f"chat.exec.start: session_id={session_id}")
            yield self._build_sse(
                "message",
                self._build_payload(session_id=session_id, event_type="start", content=""),
            )

            with self._queue_lock:
                self._drain_queue()

                def producer() -> None:
                    nonlocal producer_error
                    try:
                        with session_lock:
                            for event in self._service.stream(
                                session_id=session_id,
                                user_query=user_query,
                                context_window=context_window,
                            ):
                                self._raise_timeout_if_needed(started_at)
                                self._queue.put(
                                    {"kind": "event", "value": event},
                                    timeout=self._queue_poll_timeout,
                                )
                    except Exception as error:  # noqa: BLE001 - 소비 루프로 전달
                        producer_error = error
                    finally:
                        producer_done.set()

                producer_thread = threading.Thread(target=producer, daemon=True)
                producer_thread.start()
                try:
                    while True:
                        self._raise_timeout_if_needed(started_at)
                        item = self._queue.get(timeout=self._queue_poll_timeout)
                        if item is None:
                            if producer_done.is_set():
                                break
                            continue
                        payload = self._extract_payload(item)
                        kind = str(payload.get("kind") or "").strip()
                        if kind != "event":
                            continue
                        event = payload.get("value")
                        if not isinstance(event, dict):
                            continue
                        event_name = str(event.get("event") or "").strip()
                        node_name = str(event.get("node") or "").strip() or None
                        if event_name == "token":
                            content = str(event.get("data") or "")
                            if not content:
                                continue
                            token_count += 1
                            yield self._build_sse(
                                "message",
                                self._build_payload(
                                    session_id=session_id,
                                    event_type="token",
                                    content=content,
                                    node=node_name,
                                    event=event_name,
                                ),
                            )
                            continue
                        if event_name != "done":
                            continue
                        yield self._build_sse(
                            "message",
                            self._build_payload(
                                session_id=session_id,
                                event_type="done",
                                content="",
                                node=node_name,
                                event=event_name,
                                status="COMPLETED",
                            ),
                        )
                        done_emitted = True
                        self._llm_logger.info(
                            f"chat.exec.llm: session_id={session_id}, token_count={token_count}"
                        )
                        break
                except GeneratorExit:
                    self._service_logger.warning(f"chat.exec.cancelled: session_id={session_id}")
                    raise
                except BaseAppException as error:
                    self._service_logger.error(
                        f"chat.exec.error: session_id={session_id}, code={error.detail.code}"
                    )
                    yield self._build_sse(
                        "message",
                        self._build_payload(
                            session_id=session_id,
                            event_type="error",
                            content="",
                            status="FAILED",
                            error_message=self._format_base_error_message(error),
                        ),
                    )
                    return
                except TimeoutError as error:
                    self._service_logger.error(f"chat.exec.timeout: session_id={session_id}")
                    yield self._build_sse(
                        "message",
                        self._build_payload(
                            session_id=session_id,
                            event_type="error",
                            content="",
                            status="FAILED",
                            error_message=str(error),
                        ),
                    )
                    return
                except Exception as error:  # noqa: BLE001 - 실행 오케스트레이터 보호
                    self._service_logger.error(f"chat.exec.error: session_id={session_id}, error={error}")
                    yield self._build_sse(
                        "message",
                        self._build_payload(
                            session_id=session_id,
                            event_type="error",
                            content="",
                            status="FAILED",
                            error_message=str(error),
                        ),
                    )
                    return
                finally:
                    producer_thread.join(timeout=1.0)

            if producer_error is not None:
                if isinstance(producer_error, BaseAppException):
                    message = self._format_base_error_message(producer_error)
                else:
                    message = str(producer_error)
                self._service_logger.error(
                    f"chat.exec.error: session_id={session_id}, error={producer_error}"
                )
                yield self._build_sse(
                    "message",
                    self._build_payload(
                        session_id=session_id,
                        event_type="error",
                        content="",
                        status="FAILED",
                        error_message=message,
                    ),
                )
                return

            if not done_emitted:
                self._service_logger.error(f"chat.exec.error: session_id={session_id}, cause=done_missing")
                yield self._build_sse(
                    "message",
                    self._build_payload(
                        session_id=session_id,
                        event_type="error",
                        content="",
                        status="FAILED",
                        error_message="스트림 완료 이벤트를 생성하지 못했습니다.",
                    ),
                )
                return

            elapsed = time.monotonic() - started_at
            self._service_logger.info(
                f"chat.exec.done: session_id={session_id}, elapsed_ms={int(elapsed * 1000)}"
            )

        return generator()

    def _build_sse(self, event: str, payload: dict[str, Any]) -> str:
        body = json.dumps(payload, ensure_ascii=True)
        return f"event: {event}\ndata: {body}\n\n"

    def _build_payload(
        self,
        *,
        session_id: str,
        event_type: str,
        content: str = "",
        node: str | None = None,
        event: str | None = None,
        status: str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "type": event_type,
            "content": content,
            "node": node,
            "event": event,
            "status": status,
            "error_message": error_message,
        }

    def _get_session_lock(self, session_id: str) -> threading.Lock:
        with self._lock:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = threading.Lock()
                self._session_locks[session_id] = lock
            return lock

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

    def _resolve_queue_timeout(self) -> float:
        config = getattr(self._queue, "config", None)
        if config is None:
            return 0.2
        timeout = getattr(config, "default_timeout", None)
        if timeout is None:
            return 0.2
        return max(float(timeout), 0.01)

    def _extract_payload(self, item: Any) -> dict[str, Any]:
        if isinstance(item, QueueItem):
            payload = item.payload
            if isinstance(payload, dict):
                return payload
            return {"kind": "raw", "value": payload}
        if isinstance(item, dict):
            return item
        return {"kind": "raw", "value": item}

    def _drain_queue(self) -> None:
        queue_name = type(self._queue).__name__
        if queue_name == "RedisQueue":
            while self._queue.size() > 0:
                item = self._queue.get(timeout=0.01)
                if item is None:
                    return
            return
        while True:
            item = self._queue.get(timeout=0)
            if item is None:
                return
