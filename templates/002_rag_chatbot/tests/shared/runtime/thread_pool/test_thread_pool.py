"""
목적: 스레드풀 실행기 기본 동작을 검증한다.
설명: 태스크 제출, 데코레이터 등록, 종료 흐름을 확인한다.
디자인 패턴: 파사드, 커맨드 패턴
참조: src/chatbot/shared/runtime/thread_pool/thread_pool.py, src/chatbot/shared/runtime/thread_pool/model.py
"""

from __future__ import annotations

from chatbot.shared.runtime.thread_pool import ThreadPool, ThreadPoolConfig


def test_thread_pool_submit_and_shutdown() -> None:
    """스레드풀 제출 및 종료 동작을 검증한다."""

    pool = ThreadPool(ThreadPoolConfig(max_workers=2, thread_name_prefix="unit"))
    future = pool.submit(lambda x, y: x + y, 1, 2)

    assert future.result(timeout=1.0) == 3

    pool.shutdown()


def test_thread_pool_task_decorator() -> None:
    """데코레이터 기반 태스크 등록을 검증한다."""

    with ThreadPool(ThreadPoolConfig(max_workers=1, thread_name_prefix="unit")) as pool:
        @pool.task
        def multiply(a: int, b: int) -> int:
            return a * b

        future = multiply(3, 4)
        assert future.result(timeout=1.0) == 12
