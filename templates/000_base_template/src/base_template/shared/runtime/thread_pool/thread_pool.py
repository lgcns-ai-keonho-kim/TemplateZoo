"""
목적: 스레드풀 실행기를 제공한다.
설명: 데코레이터와 with 문을 모두 지원하며 graceful shutdown을 보장한다.
디자인 패턴: 파사드, 커맨드 패턴
참조: src/base_template/shared/runtime/thread_pool/model.py
"""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, List, Optional, TypeVar

from base_template.shared.logging import Logger, create_default_logger
from base_template.shared.runtime.thread_pool.model import TaskRecord, ThreadPoolConfig

T = TypeVar("T")


class ThreadPool:
    """스레드풀 실행기 구현체."""

    def __init__(
        self,
        config: Optional[ThreadPoolConfig] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._config = config or ThreadPoolConfig()
        self._logger = logger or create_default_logger("ThreadPool")
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: List[Future] = []
        self._lock = threading.RLock()

    def __enter__(self) -> "ThreadPool":
        """with 문 진입 시 실행기를 생성한다."""

        self._executor = ThreadPoolExecutor(
            max_workers=self._config.max_workers,
            thread_name_prefix=self._config.thread_name_prefix,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """with 문 종료 시 실행기를 종료한다."""

        self.shutdown(wait=True)

    def submit(self, fn: Callable[..., T], *args, **kwargs) -> Future[T]:
        """태스크를 제출한다."""

        with self._lock:
            if self._executor is None:
                self.__enter__()
            if self._executor is None:
                raise RuntimeError("스레드풀이 초기화되지 않았습니다.")
            record = TaskRecord(payload={"args": args, "kwargs": kwargs})
            self._logger.debug(f"태스크 제출: {record.task_id}")
            future = self._executor.submit(fn, *args, **kwargs)
            self._futures.append(future)
            future.add_done_callback(self._on_future_done)
            return future

    def task(self, fn: Callable[..., T]) -> Callable[..., Future[T]]:
        """데코레이터로 태스크를 등록한다."""

        def wrapper(*args, **kwargs) -> Future[T]:
            return self.submit(fn, *args, **kwargs)

        return wrapper

    def shutdown(self, wait: bool = True) -> None:
        """스레드풀을 종료한다."""

        with self._lock:
            if self._executor:
                self._executor.shutdown(wait=wait)
                self._executor = None
                self._futures.clear()
                self._logger.info("스레드풀이 종료되었습니다.")

    def _on_future_done(self, future: Future) -> None:
        """완료된 Future를 추적 목록에서 제거한다."""

        with self._lock:
            try:
                self._futures.remove(future)
            except ValueError:
                return
