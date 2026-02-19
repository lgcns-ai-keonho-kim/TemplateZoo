"""
목적: Redis 큐 기본 동작을 검증한다.
설명: 아이템 추가/조회/닫기 흐름과 Redis 키 정리를 확인한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/shared/runtime/queue/redis_queue.py, src/base_template/shared/runtime/queue/model.py
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from base_template.shared.runtime.queue import QueueConfig, RedisQueue

try:
    import redis
except ImportError:  # pragma: no cover - 환경 의존
    redis = None


def test_redis_queue_put_get_and_close() -> None:
    """Redis 큐 기본 동작을 검증한다."""

    url = os.getenv("REDIS_URL")
    if not url or redis is None:
        raise RuntimeError("REDIS_URL 또는 redis 패키지가 필요합니다.")

    queue_name = f"unit-{uuid4().hex[:8]}"
    queue = RedisQueue(url=url, name=queue_name, config=QueueConfig(max_size=2, default_timeout=1))
    client = redis.Redis.from_url(url)
    client.delete(queue.key)

    item = queue.put({"step": "create"})
    assert queue.size() == 1
    assert item.payload == {"step": "create"}

    loaded = queue.get(timeout=1)
    assert loaded is not None
    assert loaded.payload["step"] == "create"
    assert queue.size() == 0

    queue.close()
    with pytest.raises(RuntimeError):
        queue.put({"step": "invalid"})

    client.delete(queue.key)
