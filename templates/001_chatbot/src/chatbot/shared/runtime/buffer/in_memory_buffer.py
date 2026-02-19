"""
목적: 인메모리 이벤트 버퍼를 제공한다.
설명: 요청 단위 버킷으로 이벤트를 push/pop/cleanup 하는 구현을 제공한다.
디자인 패턴: 어댑터 패턴
참조: src/chatbot/shared/runtime/buffer/model.py
"""

from __future__ import annotations

import queue as queue_module
import threading
import time
from typing import Any

from chatbot.shared.logging import Logger, create_default_logger
from chatbot.shared.runtime.buffer.model import EventBufferConfig, StreamEventItem


class InMemoryEventBuffer:
    """인메모리 이벤트 버퍼 구현체."""

    def __init__(
        self,
        config: EventBufferConfig | None = None,
        logger: Logger | None = None,
    ) -> None:
        self._config = config or EventBufferConfig()
        self._logger = logger or create_default_logger("InMemoryEventBuffer")
        self._lock = threading.RLock()
        self._buckets: dict[str, queue_module.Queue] = {}
        self._bucket_last_touched_at: dict[str, float] = {}
        self._ttl_seconds = self._resolve_ttl_seconds()
        self._gc_interval_seconds = self._resolve_gc_interval_seconds()
        self._last_gc_ran_at = time.monotonic()

    @property
    def config(self) -> EventBufferConfig:
        """버퍼 설정을 반환한다."""

        return self._config

    def push(self, session_id: str, request_id: str, event: dict[str, Any] | StreamEventItem) -> StreamEventItem:
        """세션/요청 버킷에 이벤트를 적재한다."""

        item = self._to_item(request_id=request_id, event=event)
        key = self._bucket_key(session_id=session_id, request_id=request_id)
        now = time.monotonic()
        with self._lock:
            self._maybe_collect_expired_buckets(now=now)
            bucket = self._ensure_bucket(session_id=session_id, request_id=request_id)
            self._touch_bucket(key=key, touched_at=now)
        wait_time = self._resolve_timeout(timeout=None)
        bucket.put(item, block=True, timeout=wait_time)
        return item

    def pop(self, session_id: str, request_id: str, timeout: float | None = None) -> StreamEventItem | None:
        """세션/요청 버킷에서 이벤트를 1건 꺼낸다."""

        key = self._bucket_key(session_id=session_id, request_id=request_id)
        now = time.monotonic()
        with self._lock:
            self._maybe_collect_expired_buckets(now=now)
            bucket = self._buckets.get(key)
        wait_time = self._resolve_timeout(timeout=timeout)
        if bucket is None:
            if wait_time is not None and wait_time > 0:
                time.sleep(wait_time)
            return None
        try:
            item = bucket.get(block=True, timeout=wait_time)
        except queue_module.Empty:
            return None
        if not isinstance(item, StreamEventItem):
            return None
        with self._lock:
            if key in self._buckets:
                self._touch_bucket(key=key, touched_at=time.monotonic())
        return item

    def cleanup(self, session_id: str, request_id: str) -> None:
        """세션/요청 버킷을 정리한다."""

        key = self._bucket_key(session_id=session_id, request_id=request_id)
        with self._lock:
            self._buckets.pop(key, None)
            self._bucket_last_touched_at.pop(key, None)

    def size(self, session_id: str, request_id: str) -> int:
        """세션/요청 버킷 크기를 반환한다."""

        key = self._bucket_key(session_id=session_id, request_id=request_id)
        with self._lock:
            self._maybe_collect_expired_buckets(now=time.monotonic())
            bucket = self._buckets.get(key)
        if bucket is None:
            return 0
        return bucket.qsize()

    def _ensure_bucket(self, session_id: str, request_id: str) -> queue_module.Queue:
        key = self._bucket_key(session_id=session_id, request_id=request_id)
        bucket = self._buckets.get(key)
        if bucket is not None:
            return bucket
        bucket = queue_module.Queue(maxsize=self._config.max_size)
        self._buckets[key] = bucket
        return bucket

    def _touch_bucket(self, key: str, touched_at: float) -> None:
        self._bucket_last_touched_at[key] = touched_at

    def _maybe_collect_expired_buckets(self, now: float) -> None:
        if self._ttl_seconds is None:
            return
        elapsed_since_last_gc = now - self._last_gc_ran_at
        if elapsed_since_last_gc < self._gc_interval_seconds:
            return

        expired_keys = [
            key
            for key, touched_at in self._bucket_last_touched_at.items()
            if now - touched_at >= self._ttl_seconds
        ]
        for key in expired_keys:
            self._buckets.pop(key, None)
            self._bucket_last_touched_at.pop(key, None)

        self._last_gc_ran_at = now
        if expired_keys:
            self._logger.info(f"chat.buffer.gc: removed={len(expired_keys)}")

    def _resolve_timeout(self, timeout: float | None) -> float | None:
        if timeout is None:
            return self._config.default_timeout
        return timeout

    def _resolve_ttl_seconds(self) -> float | None:
        ttl_seconds = self._config.in_memory_ttl_seconds
        if ttl_seconds is None:
            return None
        return max(float(ttl_seconds), 1.0)

    def _resolve_gc_interval_seconds(self) -> float:
        return max(float(self._config.in_memory_gc_interval_seconds), 0.1)

    def _to_item(self, request_id: str, event: dict[str, Any] | StreamEventItem) -> StreamEventItem:
        if isinstance(event, StreamEventItem):
            if event.request_id != request_id:
                raise ValueError("event.request_id와 요청 request_id가 일치하지 않습니다.")
            return event
        node = str(event.get("node") or "").strip()
        event_name = str(event.get("event") or "").strip()
        event_request_id = str(event.get("request_id") or request_id).strip()
        if not event_name:
            raise ValueError("event 필드는 비어 있을 수 없습니다.")
        if not node:
            raise ValueError("node 필드는 비어 있을 수 없습니다.")
        if not event_request_id:
            raise ValueError("request_id 필드는 비어 있을 수 없습니다.")
        metadata = event.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("metadata는 dict 또는 None 이어야 합니다.")
        return StreamEventItem(
            event=event_name,
            data=event.get("data"),
            node=node,
            request_id=event_request_id,
            metadata=metadata,
        )

    def _bucket_key(self, session_id: str, request_id: str) -> str:
        return f"{session_id}:{request_id}"
