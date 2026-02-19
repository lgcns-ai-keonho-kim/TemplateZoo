"""
목적: 인메모리 런타임 큐를 제공한다.
설명: 블로킹/타임아웃을 지원하는 큐 구현과 로깅 주입 구조를 포함한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/shared/runtime/queue/model.py
"""

from __future__ import annotations

import queue as queue_module
from typing import Optional

from base_template.shared.logging import Logger, create_default_logger
from base_template.shared.runtime.queue.model import QueueConfig, QueueItem


class InMemoryQueue:
    """인메모리 큐 구현체."""

    _SENTINEL = object()

    def __init__(
        self,
        config: Optional[QueueConfig] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._config = config or QueueConfig()
        self._queue = queue_module.Queue(maxsize=self._config.max_size)
        self._logger = logger or create_default_logger("InMemoryQueue")
        self._closed = False

    @property
    def config(self) -> QueueConfig:
        """큐 설정을 반환한다."""

        return self._config

    def put(self, payload: object, timeout: Optional[float] = None) -> QueueItem:
        """큐에 아이템을 추가한다."""

        if self._closed:
            raise RuntimeError("이미 닫힌 큐입니다.")
        item = QueueItem(payload=payload)
        wait_time = self._resolve_timeout(timeout)
        self._queue.put(item, block=True, timeout=wait_time)
        return item

    def get(self, timeout: Optional[float] = None) -> Optional[QueueItem]:
        """큐에서 아이템을 가져온다."""

        if self._closed and self._queue.empty():
            return None
        wait_time = self._resolve_timeout(timeout)
        try:
            item = self._queue.get(block=True, timeout=wait_time)
        except queue_module.Empty:
            return None
        if item is self._SENTINEL:
            return None
        return item

    def size(self) -> int:
        """현재 큐 크기를 반환한다."""

        return self._queue.qsize()

    def close(self) -> None:
        """큐를 닫고 종료 신호를 전달한다."""

        if self._closed:
            return
        self._closed = True
        try:
            self._queue.put(self._SENTINEL, block=False)
        except queue_module.Full:
            self._logger.warning("큐가 가득 차 종료 신호를 전달하지 못했습니다.")

    def is_closed(self) -> bool:
        """큐가 닫혔는지 여부를 반환한다."""

        return self._closed

    def _resolve_timeout(self, timeout: Optional[float]) -> Optional[float]:
        if timeout is None:
            return self._config.default_timeout
        return timeout
