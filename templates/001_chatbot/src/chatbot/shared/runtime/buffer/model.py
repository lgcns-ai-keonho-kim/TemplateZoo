"""
목적: 런타임 이벤트 버퍼 모델을 정의한다.
설명: 이벤트 버퍼 설정과 스트림 이벤트 아이템 구조를 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/chatbot/shared/runtime/buffer/in_memory_buffer.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """UTC 기준 timezone-aware 현재 시각을 반환한다."""

    return datetime.now(timezone.utc)


class EventBufferConfig(BaseModel):
    """이벤트 버퍼 설정 모델이다.

    Args:
        max_size: 버퍼 최대 크기. 0이면 무제한.
        default_timeout: 기본 블로킹 대기 시간(초).
        redis_key_prefix: Redis 백엔드 키 prefix.
        redis_ttl_seconds: Redis 키 TTL(초). None이면 TTL 미적용.
        in_memory_ttl_seconds: InMemory 버킷 TTL(초). None이면 TTL 미적용.
        in_memory_gc_interval_seconds: InMemory GC 주기(초).
    """

    max_size: int = Field(default=0, ge=0)
    default_timeout: float | None = Field(default=None, ge=0)
    redis_key_prefix: str = Field(default="chat:stream")
    redis_ttl_seconds: int | None = Field(default=600, ge=1)
    in_memory_ttl_seconds: int | None = Field(default=600, ge=1)
    in_memory_gc_interval_seconds: float = Field(default=30.0, gt=0)


class StreamEventItem(BaseModel):
    """이벤트 버퍼에 저장되는 내부 이벤트 모델이다.

    Args:
        item_id: 이벤트 아이템 식별자.
        event: 내부 이벤트 타입(start|token|done|error).
        data: 이벤트 데이터 본문.
        node: 이벤트를 생성한 노드 이름.
        request_id: 요청 식별자.
        metadata: 부가 메타데이터(선택).
        created_at: 생성 시각.
    """

    item_id: str = Field(default_factory=lambda: str(uuid4()))
    event: str = Field(..., min_length=1)
    data: Any = None
    node: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=_utc_now)
