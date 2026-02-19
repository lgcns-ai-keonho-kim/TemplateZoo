"""
목적: InMemoryEventBuffer의 만료/정리 동작을 검증한다.
설명: TTL과 GC 주기에 따라 버킷이 정리되는지 확인한다.
디자인 패턴: 상태 기반 단위 테스트
참조: src/chatbot/shared/runtime/buffer/in_memory_buffer.py
"""

from __future__ import annotations

import time

from chatbot.shared.runtime.buffer import EventBufferConfig, InMemoryEventBuffer


def test_in_memory_event_buffer_gc_removes_expired_bucket() -> None:
    """TTL이 지난 버킷은 GC 실행 시 정리되어야 한다."""

    buffer = InMemoryEventBuffer(
        config=EventBufferConfig(
            default_timeout=0.01,
            in_memory_ttl_seconds=1,
            in_memory_gc_interval_seconds=0.05,
        )
    )
    session_id = "s1"
    request_id = "r1"
    buffer.push(
        session_id=session_id,
        request_id=request_id,
        event={"event": "token", "data": "안녕", "node": "response", "request_id": request_id},
    )
    assert buffer.size(session_id=session_id, request_id=request_id) == 1

    time.sleep(1.1)

    assert buffer.size(session_id=session_id, request_id=request_id) == 0
    assert buffer.pop(session_id=session_id, request_id=request_id, timeout=0.01) is None


def test_in_memory_event_buffer_preserves_bucket_when_ttl_disabled() -> None:
    """TTL이 비활성화되면 GC가 버킷을 제거하지 않아야 한다."""

    buffer = InMemoryEventBuffer(
        config=EventBufferConfig(
            default_timeout=0.01,
            in_memory_ttl_seconds=None,
            in_memory_gc_interval_seconds=0.05,
        )
    )
    session_id = "s2"
    request_id = "r2"
    buffer.push(
        session_id=session_id,
        request_id=request_id,
        event={"event": "token", "data": "hello", "node": "response", "request_id": request_id},
    )

    time.sleep(0.2)

    assert buffer.size(session_id=session_id, request_id=request_id) == 1
