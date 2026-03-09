"""
목적: Redis 큐 기본 동작을 검증한다.
설명: 아이템 추가/조회/닫기 흐름과 Redis 키 정리를 확인한다.
디자인 패턴: 어댑터 패턴
참조: src/text_to_sql/shared/runtime/queue/redis_queue.py, src/text_to_sql/shared/runtime/queue/model.py
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
import redis

from text_to_sql.shared.runtime.queue import QueueConfig, RedisQueue


def test_redis_queue_put_get_and_close() -> None:
    """Redis 큐 기본 동작을 검증한다."""

    host = str(os.getenv("REDIS_HOST") or "").strip()
    port_raw = str(os.getenv("REDIS_PORT", "6379") or "").strip()
    db_raw = str(os.getenv("REDIS_DB", "0") or "").strip()
    password = str(os.getenv("REDIS_PW") or "").strip()
    if not host:
        raise RuntimeError("REDIS_HOST 환경 변수가 필요합니다.")
    if not port_raw.isdigit():
        raise RuntimeError("REDIS_PORT는 정수여야 합니다.")
    if not db_raw.isdigit():
        raise RuntimeError("REDIS_DB는 정수여야 합니다.")
    port = int(port_raw)
    db = int(db_raw)

    if password:
        url = f"redis://:{password}@{host}:{port}/{db}"
    else:
        url = f"redis://{host}:{port}/{db}"

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
