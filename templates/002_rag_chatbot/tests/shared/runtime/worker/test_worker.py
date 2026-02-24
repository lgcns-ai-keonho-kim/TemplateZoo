"""
목적: 워커 기본 실행 흐름을 검증한다.
설명: 데코레이터 등록과 with 구문 실행을 통해 큐 아이템이 처리되는지 확인한다.
디자인 패턴: 템플릿 메서드, 커맨드 패턴
참조: src/rag_chatbot/shared/runtime/worker/worker.py, src/rag_chatbot/shared/runtime/queue/in_memory_queue.py
"""

from __future__ import annotations

import threading

from rag_chatbot.shared.runtime.queue import InMemoryQueue
from rag_chatbot.shared.runtime.worker import Worker, WorkerConfig, WorkerState


def test_worker_processes_items_with_context_manager() -> None:
    """워커가 큐 아이템을 처리하는지 검증한다."""

    queue = InMemoryQueue()
    worker = Worker(queue, config=WorkerConfig(name="unit-worker", poll_timeout=0.05))
    processed = []
    done = threading.Event()

    @worker
    def handler(item) -> None:
        processed.append(item.payload)
        done.set()

    with worker:
        queue.put({"id": 1})
        assert done.wait(1.0) is True

    assert processed == [{"id": 1}]
    assert worker.state == WorkerState.STOPPED
