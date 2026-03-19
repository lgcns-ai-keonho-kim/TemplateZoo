"""
목적: ServiceExecutor 보조 동작 믹스인을 제공한다.
설명: 영속 후처리, 이벤트 정규화/직렬화, 상태/타임아웃 보조 로직을 분리한다.
디자인 패턴: 믹스인
참조: src/tool_proxy_agent/shared/chat/services/service_executor.py
"""

from __future__ import annotations

import json
import queue as queue_module
import threading
import time
from collections.abc import Mapping
from typing import Any

from tool_proxy_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)
from tool_proxy_agent.shared.runtime.buffer import StreamEventItem
from tool_proxy_agent.shared.runtime.queue import QueueItem


class _ServiceExecutorSupportMixin:
    """ServiceExecutor의 내부 보조 메서드를 제공한다."""

    _persist_stop_event: Any
    _persist_queue: Any
    _job_poll_timeout: float
    _PERSIST_STOP: str
    _service_logger: Any
    _persist_retry_limit: int
    _persist_retry_delay_seconds: float
    _service: Any
    _EVENT_TOKEN: str
    _EVENT_REFERENCES: str
    _EVENT_DONE: str
    _EVENT_ERROR: str
    _event_buffer: Any
    _ALLOWED_EVENT_TYPES: set[str]
    _lock: Any
    _session_locks: dict[str, threading.Lock]
    _ALLOWED_STATUS: set[str]
    _session_statuses: dict[str, str]
    _STATUS_RUNNING: str
    _STATUS_QUEUED: str
    _timeout_seconds: float
    _job_queue: Any

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

    def _retry_persist_task(
        self, task: dict[str, Any], attempt: int, reason: str
    ) -> None:
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
            detail = ExceptionDetail(
                code="CHAT_SESSION_NOT_FOUND", cause=f"session_id={candidate}"
            )
            raise BaseAppException("요청한 세션을 찾을 수 없습니다.", detail)
        return candidate

    def _normalize_graph_event(self, event: Any) -> dict[str, Any] | None:
        """그래프 이벤트를 공개 이벤트 스키마로 정규화한다."""

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
                "node": node,
                "data": payload,
                "metadata": metadata,
            }

        if event_name in {"tool_start", "tool_result", "tool_error"}:
            payload: dict[str, Any]
            if isinstance(data, Mapping):
                payload = {str(key): value for key, value in data.items()}
            else:
                payload = {"value": data}

            merged_metadata = self._merge_metadata(
                metadata=metadata if isinstance(metadata, dict) else None,
                patch={
                    "tool_call_id": str(payload.get("tool_call_id") or ""),
                    "retry_for": str(payload.get("retry_for") or ""),
                    "tool_name": str(payload.get("tool_name") or ""),
                    "required": bool(payload.get("required") is True),
                    "attempt": int(payload.get("attempt") or 0),
                },
            )
            return {
                "event": event_name,
                "node": node or "tool_exec",
                "data": payload,
                "metadata": merged_metadata,
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

    def _build_public_payload(
        self, session_id: str, item: StreamEventItem
    ) -> dict[str, Any]:
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
