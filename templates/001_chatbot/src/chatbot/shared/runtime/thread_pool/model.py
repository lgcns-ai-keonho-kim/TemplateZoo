"""
목적: 스레드풀 모델을 정의한다.
설명: 스레드풀 설정과 태스크 모델을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/chatbot/shared/runtime/thread_pool/thread_pool.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ThreadPoolConfig(BaseModel):
    """스레드풀 설정 모델이다.

    Args:
        max_workers: 최대 스레드 수.
        thread_name_prefix: 스레드 이름 접두사.
    """

    max_workers: int = Field(default=4, ge=1)
    thread_name_prefix: str = Field(default="thread-pool")


def _utc_now() -> datetime:
    """UTC 기준의 timezone-aware 시간을 반환한다."""

    return datetime.now(timezone.utc)


class TaskRecord(BaseModel):
    """태스크 레코드 모델이다.

    Args:
        task_id: 태스크 식별자.
        payload: 태스크 입력 데이터.
        submitted_at: 제출 시각.
        metadata: 추가 메타데이터.
    """

    task_id: str = Field(default_factory=lambda: str(uuid4()))
    payload: Optional[Any] = None
    submitted_at: datetime = Field(default_factory=_utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
