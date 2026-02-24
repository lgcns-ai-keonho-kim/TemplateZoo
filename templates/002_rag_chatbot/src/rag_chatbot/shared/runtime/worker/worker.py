"""
목적: 큐 소비용 워커를 제공한다.
설명: 데코레이터와 with 문을 모두 지원하며 로깅/오류 처리/재시도를 포함한다.
디자인 패턴: 템플릿 메서드, 커맨드 패턴
참조: src/rag_chatbot/shared/runtime/queue/in_memory_queue.py, src/rag_chatbot/shared/runtime/worker/model.py
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

from rag_chatbot.shared.logging import Logger, create_default_logger
from rag_chatbot.shared.runtime.queue import InMemoryQueue, QueueItem
from rag_chatbot.shared.runtime.worker.model import WorkerConfig, WorkerState

Handler = Callable[[QueueItem], None]


class Worker:
    """큐를 소비하는 워커 구현체."""

    def __init__(
        self,
        queue: InMemoryQueue,
        config: Optional[WorkerConfig] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._queue = queue
        self._config = config or WorkerConfig()
        self._logger = logger or create_default_logger(self._config.name)
        self._handler: Optional[Handler] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._state = WorkerState.IDLE

    @property
    def state(self) -> WorkerState:
        """현재 워커 상태를 반환한다."""

        return self._state

    def __call__(self, handler: Handler) -> Handler:
        """데코레이터로 핸들러를 등록한다."""

        self._handler = handler
        return handler

    def start(self) -> None:
        """워커 스레드를 시작한다."""

        if self._thread and self._thread.is_alive():
            return
        if self._handler is None:
            raise ValueError("워커 핸들러가 등록되지 않았습니다.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._state = WorkerState.RUNNING
        self._logger.info("워커가 시작되었습니다.")

    def stop(self) -> None:
        """워커를 중지한다."""

        self._stop_event.set()
        self._queue.close()
        if self._thread:
            self._thread.join(timeout=3)
        self._state = WorkerState.STOPPED
        self._logger.info("워커가 중지되었습니다.")

    def __enter__(self) -> "Worker":
        """with 문 진입 시 워커를 시작한다."""

        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """with 문 종료 시 워커를 중지한다."""

        self.stop()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            item = self._queue.get(timeout=self._config.poll_timeout)
            if item is None:
                continue
            self._process_item(item)

    def _process_item(self, item: QueueItem) -> None:
        retries = 0
        while True:
            try:
                if self._handler is None:
                    raise ValueError("워커 핸들러가 없습니다.")
                self._handler(item)
                return
            except Exception as error:  # noqa: BLE001 - 로깅을 위해 포괄 처리
                retries += 1
                self._logger.error(f"워커 처리 실패: {error}")
                if retries > self._config.max_retries:
                    self._state = WorkerState.ERROR
                    if self._config.stop_on_error:
                        self._stop_event.set()
                    return
