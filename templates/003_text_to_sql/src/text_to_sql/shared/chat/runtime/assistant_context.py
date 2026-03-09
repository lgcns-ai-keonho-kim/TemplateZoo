"""
목적: 직전 assistant 응답 컨텍스트 캐시 구현체를 제공한다.
설명: 세션별 마지막 assistant 응답을 InMemory/Redis 백엔드로 보관해
      후속 질의 분기에서 즉시 재사용할 수 있게 한다.
디자인 패턴: 포트-어댑터(Protocol + 구현체)
참조: src/text_to_sql/shared/chat/services/service_executor.py
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

try:
    import redis as redis_module
except Exception:  # pragma: no cover - redis 미설치 환경 보호
    redis_module: Any | None = None

from text_to_sql.shared.logging import Logger, create_default_logger


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_answer_source_meta(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items()}


@dataclass(frozen=True)
class AssistantContext:
    """세션별 직전 assistant 컨텍스트 모델."""

    session_id: str
    request_id: str
    content: str
    answer_source_meta: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utc_now)


class AssistantContextStore(Protocol):
    """직전 assistant 컨텍스트 저장소 포트."""

    def set(self, context: AssistantContext) -> None:
        """세션별 마지막 컨텍스트를 저장한다."""

    def get(self, session_id: str) -> AssistantContext | None:
        """세션의 마지막 컨텍스트를 조회한다."""

    def clear_session(self, session_id: str) -> None:
        """세션 컨텍스트를 제거한다."""

    def close(self) -> None:
        """저장소 리소스를 정리한다."""


@dataclass
class _InMemoryEntry:
    context: AssistantContext
    touched_at: float


class InMemoryAssistantContextStore:
    """InMemory 기반 assistant 컨텍스트 캐시."""

    def __init__(
        self,
        *,
        ttl_seconds: int = 1800,
        max_sessions: int = 2000,
        logger: Logger | None = None,
    ) -> None:
        self._ttl_seconds = max(1, int(ttl_seconds))
        self._max_sessions = max(1, int(max_sessions))
        self._logger = logger or create_default_logger("InMemoryAssistantContextStore")
        self._lock = threading.RLock()
        self._entries: OrderedDict[str, _InMemoryEntry] = OrderedDict()

    def set(self, context: AssistantContext) -> None:
        session_id = str(context.session_id or "").strip()
        if not session_id:
            return
        now = time.monotonic()
        with self._lock:
            self._collect_expired_locked(now=now)
            self._entries.pop(session_id, None)
            self._entries[session_id] = _InMemoryEntry(
                context=self._copy_context(context),
                touched_at=now,
            )
            self._entries.move_to_end(session_id, last=True)
            self._enforce_lru_limit_locked()

    def get(self, session_id: str) -> AssistantContext | None:
        candidate = str(session_id or "").strip()
        if not candidate:
            return None
        now = time.monotonic()
        with self._lock:
            self._collect_expired_locked(now=now)
            entry = self._entries.get(candidate)
            if entry is None:
                return None
            entry.touched_at = now
            self._entries.move_to_end(candidate, last=True)
            return self._copy_context(entry.context)

    def clear_session(self, session_id: str) -> None:
        candidate = str(session_id or "").strip()
        if not candidate:
            return
        with self._lock:
            self._entries.pop(candidate, None)

    def close(self) -> None:
        with self._lock:
            self._entries.clear()

    def _collect_expired_locked(self, *, now: float) -> None:
        expired: list[str] = []
        for session_id, entry in self._entries.items():
            if now - entry.touched_at >= self._ttl_seconds:
                expired.append(session_id)
        for session_id in expired:
            self._entries.pop(session_id, None)
        if expired:
            self._logger.debug(
                "assistant.context.gc: expired_sessions=%s" % len(expired)
            )

    def _enforce_lru_limit_locked(self) -> None:
        overflow = len(self._entries) - self._max_sessions
        if overflow <= 0:
            return
        for _ in range(overflow):
            self._entries.popitem(last=False)
        self._logger.debug("assistant.context.lru: evicted_sessions=%s" % overflow)

    def _copy_context(self, context: AssistantContext) -> AssistantContext:
        return AssistantContext(
            session_id=str(context.session_id),
            request_id=str(context.request_id),
            content=str(context.content),
            answer_source_meta=deepcopy(
                _normalize_answer_source_meta(context.answer_source_meta)
            ),
            created_at=context.created_at,
        )


class RedisAssistantContextStore:
    """Redis 기반 assistant 컨텍스트 캐시."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        ttl_seconds: int = 1800,
        max_sessions: int = 2000,
        key_prefix: str = "chat:assistant_ctx",
        lru_index_key: str = "chat:assistant_ctx:lru",
        logger: Logger | None = None,
    ) -> None:
        if redis_module is None:
            raise RuntimeError("redis 패키지가 설치되어 있지 않습니다.")
        self._host = str(host or "").strip()
        if not self._host:
            raise RuntimeError("Redis host가 비어 있습니다.")
        self._port = int(port)
        if self._port <= 0:
            raise RuntimeError("Redis port는 1 이상의 정수여야 합니다.")
        self._db = int(db)
        if self._db < 0:
            raise RuntimeError("Redis db는 0 이상의 정수여야 합니다.")
        normalized_password = str(password or "").strip()
        self._password = normalized_password or None
        self._ttl_seconds = max(1, int(ttl_seconds))
        self._max_sessions = max(1, int(max_sessions))
        self._key_prefix = str(key_prefix or "").strip() or "chat:assistant_ctx"
        self._lru_index_key = (
            str(lru_index_key or "").strip() or "chat:assistant_ctx:lru"
        )
        self._logger = logger or create_default_logger("RedisAssistantContextStore")
        self._client: Any | None = None

    def ping(self) -> None:
        client = self._require_client()
        result = client.ping()
        if result is not True:
            raise RuntimeError(
                "Redis assistant context cache ping 응답이 비정상입니다."
            )

    def set(self, context: AssistantContext) -> None:
        session_id = str(context.session_id or "").strip()
        if not session_id:
            return
        client = self._require_client()
        key = self._context_key(session_id=session_id)
        now_ts = time.time()
        payload = self._encode_context(context)

        pipeline = client.pipeline()
        pipeline.set(key, payload, ex=self._ttl_seconds)
        pipeline.zadd(self._lru_index_key, {session_id: now_ts})
        pipeline.expire(self._lru_index_key, self._ttl_seconds * 4)
        pipeline.execute()
        self._trim_lru(client=client)

    def get(self, session_id: str) -> AssistantContext | None:
        candidate = str(session_id or "").strip()
        if not candidate:
            return None
        client = self._require_client()
        key = self._context_key(session_id=candidate)
        raw = client.get(key)
        if raw is None:
            client.zrem(self._lru_index_key, candidate)
            return None
        context = self._decode_context(session_id=candidate, raw=raw)
        now_ts = time.time()
        pipeline = client.pipeline()
        pipeline.zadd(self._lru_index_key, {candidate: now_ts})
        pipeline.expire(key, self._ttl_seconds)
        pipeline.expire(self._lru_index_key, self._ttl_seconds * 4)
        pipeline.execute()
        self._trim_lru(client=client)
        return context

    def clear_session(self, session_id: str) -> None:
        candidate = str(session_id or "").strip()
        if not candidate:
            return
        client = self._require_client()
        key = self._context_key(session_id=candidate)
        pipeline = client.pipeline()
        pipeline.delete(key)
        pipeline.zrem(self._lru_index_key, candidate)
        pipeline.execute()

    def close(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return
        close_fn = getattr(client, "close", None)
        if callable(close_fn):
            close_fn()

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        assert redis_module is not None
        self._client = redis_module.Redis(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
        )
        self._logger.info(
            "Redis assistant context cache 연결이 초기화되었습니다. "
            f"(host={self._host}, port={self._port}, db={self._db})"
        )

    def _require_client(self) -> Any:
        self._ensure_client()
        if self._client is None:
            raise RuntimeError(
                "Redis assistant context cache 연결이 초기화되지 않았습니다."
            )
        return self._client

    def _trim_lru(self, *, client: Any) -> None:
        overflow = int(client.zcard(self._lru_index_key)) - self._max_sessions
        if overflow <= 0:
            return
        stale_members = client.zrange(self._lru_index_key, 0, overflow - 1)
        if not isinstance(stale_members, list):
            return
        pipeline = client.pipeline()
        for raw_member in stale_members:
            session_id = self._decode_member(raw_member)
            if not session_id:
                continue
            pipeline.delete(self._context_key(session_id=session_id))
        pipeline.zremrangebyrank(self._lru_index_key, 0, overflow - 1)
        pipeline.execute()
        self._logger.debug(
            "assistant.context.redis.lru: evicted_sessions=%s" % overflow
        )

    def _context_key(self, *, session_id: str) -> str:
        return f"{self._key_prefix}:{session_id}"

    def _encode_context(self, context: AssistantContext) -> str:
        payload = {
            "request_id": str(context.request_id),
            "content": str(context.content),
            "answer_source_meta": _normalize_answer_source_meta(
                context.answer_source_meta
            ),
            "created_at": context.created_at.isoformat(),
        }
        return json.dumps(payload, ensure_ascii=True)

    def _decode_context(self, *, session_id: str, raw: object) -> AssistantContext:
        if isinstance(raw, bytes):
            raw_text = raw.decode("utf-8", errors="replace")
        else:
            raw_text = str(raw or "")
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        created_at = _utc_now()
        created_raw = str(payload.get("created_at") or "").strip()
        if created_raw:
            try:
                parsed = datetime.fromisoformat(created_raw)
                if parsed.tzinfo is None:
                    created_at = parsed.replace(tzinfo=timezone.utc)
                else:
                    created_at = parsed
            except ValueError:
                created_at = _utc_now()
        return AssistantContext(
            session_id=session_id,
            request_id=str(payload.get("request_id") or ""),
            content=str(payload.get("content") or ""),
            answer_source_meta=_normalize_answer_source_meta(
                payload.get("answer_source_meta")
            ),
            created_at=created_at,
        )

    def _decode_member(self, raw_member: object) -> str:
        if isinstance(raw_member, bytes):
            return raw_member.decode("utf-8", errors="replace").strip()
        return str(raw_member or "").strip()


__all__ = [
    "AssistantContext",
    "AssistantContextStore",
    "InMemoryAssistantContextStore",
    "RedisAssistantContextStore",
]
