"""
목적: 런타임 큐 모델을 정의한다.
설명: 큐 설정과 큐 아이템 구조를 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/chatbot/shared/runtime/queue/in_memory_queue.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class QueueConfig(BaseModel):
    """인메모리 큐 설정 모델이다.

    Args:
        max_size: 큐 최대 크기. 0이면 무제한.
        default_timeout: 기본 블로킹 대기 시간(초).
    """

    max_size: int = Field(default=0, ge=0)
    default_timeout: Optional[float] = Field(default=None, ge=0)


def _utc_now() -> datetime:
    """UTC 기준의 timezone-aware 시간을 반환한다."""

    return datetime.now(timezone.utc)


class QueueItem(BaseModel):
    """큐 아이템 모델이다.

    Args:
        item_id: 큐 아이템 식별자.
        payload: 실제 처리 데이터.
        created_at: 생성 시각.
    """

    item_id: str = Field(default_factory=lambda: str(uuid4()))
    payload: Any
    created_at: datetime = Field(default_factory=_utc_now)
