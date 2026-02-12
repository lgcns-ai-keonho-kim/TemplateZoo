"""
목적: Redis 기반 이벤트 버퍼를 제공한다.
설명: 내부 이벤트를 요청 단위 Redis 리스트에 저장하고 BLPOP으로 소비한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/shared/runtime/buffer/model.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from base_template.shared.logging import Logger, create_default_logger
from base_template.shared.runtime.buffer.model import EventBufferConfig, StreamEventItem

try:
    import redis
except ImportError:  # pragma: no cover - 환경 의존 로딩
    redis = None


class RedisEventBuffer:
    """Redis 이벤트 버퍼 구현체."""

    def __init__(
        self,
        url: str,
        config: EventBufferConfig | None = None,
        logger: Logger | None = None,
    ) -> None:
        self._url = url
        self._config = config or EventBufferConfig()
        self._logger = logger or create_default_logger("RedisEventBuffer")
        self._client = None

    @property
    def config(self) -> EventBufferConfig:
        """버퍼 설정을 반환한다."""

        return self._config

    def push(self, session_id: str, request_id: str, event: dict[str, Any] | StreamEventItem) -> StreamEventItem:
        """요청 단위 키에 이벤트를 적재한다."""

        self._ensure_client()
        item = self._to_item(request_id=request_id, event=event)
        key = self._key(session_id=session_id, request_id=request_id)
        self._client.rpush(key, self._encode_item(item))
        ttl = self._config.redis_ttl_seconds
        if ttl is not None:
            self._client.expire(key, int(ttl))
        return item

    def pop(self, session_id: str, request_id: str, timeout: float | None = None) -> StreamEventItem | None:
        """요청 단위 키에서 이벤트를 1건 꺼낸다."""

        self._ensure_client()
        key = self._key(session_id=session_id, request_id=request_id)
        wait_time = self._resolve_timeout(timeout=timeout)
        result = self._blocking_pop(key=key, timeout=wait_time)
        if result is None:
            return None
        _, raw = result
        return self._decode_item(raw)

    def cleanup(self, session_id: str, request_id: str) -> None:
        """요청 단위 키를 정리한다."""

        self._ensure_client()
        key = self._key(session_id=session_id, request_id=request_id)
        self._client.delete(key)

    def size(self, session_id: str, request_id: str) -> int:
        """요청 단위 키의 현재 리스트 길이를 반환한다."""

        self._ensure_client()
        key = self._key(session_id=session_id, request_id=request_id)
        return int(self._client.llen(key))

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        if redis is None:
            raise RuntimeError("redis 패키지가 설치되어 있지 않습니다.")
        self._client = redis.Redis.from_url(self._url)
        self._logger.info("Redis 이벤트 버퍼 연결이 초기화되었습니다.")

    def _resolve_timeout(self, timeout: float | None) -> float | None:
        if timeout is None:
            return self._config.default_timeout
        return timeout

    def _blocking_pop(self, key: str, timeout: float | None):
        wait_time = 0 if timeout is None else max(timeout, 0)
        try:
            return self._client.blpop(key, timeout=wait_time)
        except TypeError:
            wait_time_int = 0 if timeout is None else max(int(timeout), 1)
            return self._client.blpop(key, timeout=wait_time_int)

    def _to_item(self, request_id: str, event: dict[str, Any] | StreamEventItem) -> StreamEventItem:
        if isinstance(event, StreamEventItem):
            if event.request_id != request_id:
                raise ValueError("event.request_id와 요청 request_id가 일치하지 않습니다.")
            return event
        node = str(event.get("node") or "").strip()
        event_name = str(event.get("event") or "").strip()
        event_request_id = str(event.get("request_id") or request_id).strip()
        if not event_name:
            raise ValueError("event 필드는 비어 있을 수 없습니다.")
        if not node:
            raise ValueError("node 필드는 비어 있을 수 없습니다.")
        if not event_request_id:
            raise ValueError("request_id 필드는 비어 있을 수 없습니다.")
        metadata = event.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("metadata는 dict 또는 None 이어야 합니다.")
        return StreamEventItem(
            event=event_name,
            data=event.get("data"),
            node=node,
            request_id=event_request_id,
            metadata=metadata,
        )

    def _encode_item(self, item: StreamEventItem) -> str:
        payload = {
            "item_id": item.item_id,
            "event": item.event,
            "data": item.data,
            "node": item.node,
            "request_id": item.request_id,
            "metadata": item.metadata,
            "created_at": item.created_at.isoformat(),
        }
        try:
            return json.dumps(payload, ensure_ascii=True)
        except TypeError as exc:
            raise ValueError("JSON 직렬화가 불가능한 이벤트입니다.") from exc

    def _decode_item(self, raw: bytes) -> StreamEventItem:
        try:
            data = json.loads(raw.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("이벤트 버퍼 데이터 디코딩에 실패했습니다.") from exc
        created_at = self._parse_datetime(data.get("created_at"))
        return StreamEventItem(
            item_id=str(data.get("item_id") or ""),
            event=str(data.get("event") or ""),
            data=data.get("data"),
            node=str(data.get("node") or ""),
            request_id=str(data.get("request_id") or ""),
            metadata=data.get("metadata"),
            created_at=created_at,
        )

    def _parse_datetime(self, raw: str | None) -> datetime:
        if not raw:
            return datetime.now(timezone.utc)
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return datetime.now(timezone.utc)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _key(self, session_id: str, request_id: str) -> str:
        prefix = self._config.redis_key_prefix.strip() or "chat:stream"
        return f"{prefix}:{session_id}:{request_id}"

