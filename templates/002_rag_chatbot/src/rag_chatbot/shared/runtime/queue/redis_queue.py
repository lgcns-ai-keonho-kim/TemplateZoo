"""
목적: Redis 기반 런타임 큐를 제공한다.
설명: QueueItem 모델을 직렬화해 Redis 리스트에 저장하고 블로킹 팝으로 소비한다.
디자인 패턴: 어댑터 패턴
참조: src/rag_chatbot/shared/runtime/queue/model.py
"""

from __future__ import annotations

import json
import queue as queue_module
import time
from collections.abc import Awaitable
from datetime import datetime, timezone
from typing import Any, Optional

from rag_chatbot.shared.logging import Logger, create_default_logger
from rag_chatbot.shared.runtime.queue.model import QueueConfig, QueueItem

redis_module: Any | None
try:
    import redis as _redis_module
except ImportError:  # pragma: no cover - 환경 의존 로딩
    redis_module = None
else:  # pragma: no cover - 환경 의존 로딩
    redis_module = _redis_module


class RedisQueue:
    """Redis 기반 큐 구현체."""

    def __init__(
        self,
        url: str,
        name: str = "default",
        config: Optional[QueueConfig] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._url = url
        self._name = name
        self._queue_key = f"queue:{name}"
        self._config = config or QueueConfig()
        self._logger = logger or create_default_logger(f"RedisQueue[{name}]")
        self._client: Any | None = None
        self._closed = False

    @property
    def config(self) -> QueueConfig:
        """큐 설정을 반환한다."""

        return self._config

    @property
    def name(self) -> str:
        """큐 이름을 반환한다."""

        return self._name

    @property
    def key(self) -> str:
        """Redis 키를 반환한다."""

        return self._queue_key

    def put(self, payload: object, timeout: Optional[float] = None) -> QueueItem:
        """큐에 아이템을 추가한다."""

        if self._closed:
            raise RuntimeError("이미 닫힌 큐입니다.")
        client = self._require_client()
        wait_time = self._resolve_timeout(timeout)
        self._wait_for_capacity(wait_time)
        item = QueueItem(payload=payload)
        client.rpush(self._queue_key, self._encode_item(item))
        return item

    def get(self, timeout: Optional[float] = None) -> Optional[QueueItem]:
        """큐에서 아이템을 가져온다."""

        if self._closed and self.size() == 0:
            return None
        wait_time = self._resolve_timeout(timeout)
        result = self._blocking_pop(wait_time)
        if result is None:
            return None
        raw_value = result[1]
        if isinstance(raw_value, bytes):
            return self._decode_item(raw_value)
        if isinstance(raw_value, bytearray):
            return self._decode_item(bytes(raw_value))
        if isinstance(raw_value, str):
            return self._decode_item(raw_value.encode())
        raise ValueError("Redis BLPOP 결과 형식이 올바르지 않습니다.")

    def size(self) -> int:
        """현재 큐 크기를 반환한다."""

        client = self._require_client()
        size = client.llen(self._queue_key)
        if isinstance(size, int):
            return size
        if isinstance(size, (float, str)):
            try:
                return int(size)
            except ValueError:
                return 0
        return 0

    def close(self) -> None:
        """큐를 닫는다."""

        if self._closed:
            return
        self._closed = True
        self._logger.info("Redis 큐가 닫혔습니다.")

    def is_closed(self) -> bool:
        """큐가 닫혔는지 여부를 반환한다."""

        return self._closed

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        if redis_module is None:
            raise RuntimeError("redis 패키지가 설치되어 있지 않습니다.")
        self._client = redis_module.Redis.from_url(self._url)
        self._logger.info("Redis 큐 연결이 초기화되었습니다.")

    def _require_client(self) -> Any:
        self._ensure_client()
        if self._client is None:
            raise RuntimeError("Redis 큐 연결이 초기화되지 않았습니다.")
        return self._client

    def _resolve_timeout(self, timeout: Optional[float]) -> Optional[float]:
        if timeout is None:
            return self._config.default_timeout
        return timeout

    def _wait_for_capacity(self, timeout: Optional[float]) -> None:
        max_size = self._config.max_size
        if max_size <= 0:
            return
        deadline = time.monotonic() + timeout if timeout is not None else None
        while self.size() >= max_size:
            if deadline is not None and time.monotonic() >= deadline:
                raise queue_module.Full("큐가 가득 차서 추가할 수 없습니다.")
            time.sleep(0.05)

    def _blocking_pop(self, timeout: Optional[float]):
        client = self._require_client()
        wait_time = 0 if timeout is None else max(timeout, 0)
        try:
            result = client.blpop([self._queue_key], timeout=wait_time)
        except TypeError:
            wait_time_int = 0 if timeout is None else max(int(timeout), 1)
            result = client.blpop([self._queue_key], timeout=wait_time_int)
        if isinstance(result, Awaitable):
            raise RuntimeError("비동기 Redis 클라이언트는 지원하지 않습니다.")
        if result is None:
            return None
        if not isinstance(result, (list, tuple)) or len(result) < 2:
            raise ValueError("Redis BLPOP 결과 형식이 올바르지 않습니다.")
        key_raw = result[0]
        value_raw = result[1]
        key_bytes = key_raw if isinstance(key_raw, bytes) else str(key_raw).encode()
        value_bytes = value_raw if isinstance(value_raw, bytes) else str(value_raw).encode()
        return key_bytes, value_bytes

    def _encode_item(self, item: QueueItem) -> str:
        payload = {
            "item_id": item.item_id,
            "payload": item.payload,
            "created_at": item.created_at.isoformat(),
        }
        try:
            return json.dumps(payload)
        except TypeError as exc:
            raise ValueError("JSON 직렬화가 불가능한 payload입니다.") from exc

    def _decode_item(self, raw: bytes) -> QueueItem:
        try:
            data = json.loads(raw.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("큐 데이터 디코딩에 실패했습니다.") from exc
        created_at = self._parse_datetime(data.get("created_at"))
        return QueueItem(
            item_id=data.get("item_id"),
            payload=data.get("payload"),
            created_at=created_at,
        )

    def _parse_datetime(self, raw: Optional[str]) -> datetime:
        if not raw:
            return datetime.now(timezone.utc)
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return datetime.now(timezone.utc)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
