"""
목적: 인메모리 큐 기본 동작을 검증한다.
설명: 아이템 추가/조회, 종료 동작, 크기 계산을 확인한다.
디자인 패턴: 어댑터 패턴
참조: src/rag_chatbot/shared/runtime/queue/in_memory_queue.py, src/rag_chatbot/shared/runtime/queue/model.py
"""

from __future__ import annotations

import pytest

from rag_chatbot.shared.runtime.queue import InMemoryQueue, QueueConfig


def test_inmemory_queue_put_get_and_close() -> None:
    """큐 기본 동작을 검증한다."""

    queue = InMemoryQueue(config=QueueConfig(max_size=2, default_timeout=0.1))

    item = queue.put({"step": "create"})

    assert queue.size() == 1
    assert item.payload == {"step": "create"}

    loaded = queue.get(timeout=0.1)
    assert loaded is not None
    assert loaded.payload["step"] == "create"
    assert queue.size() == 0

    queue.close()
    assert queue.is_closed() is True
    assert queue.get(timeout=0.1) is None


def test_inmemory_queue_put_after_close_raises() -> None:
    """닫힌 큐에 추가 시 오류가 발생하는지 확인한다."""

    queue = InMemoryQueue()
    queue.close()

    with pytest.raises(RuntimeError):
        queue.put({"step": "invalid"})
