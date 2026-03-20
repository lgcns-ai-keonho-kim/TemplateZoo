"""
목적: 워커 설정 및 상태 모델을 정의한다.
설명: 워커 실행 파라미터와 상태 값을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체
참조: src/one_shot_agent/shared/runtime/worker/worker.py
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WorkerState(str, Enum):
    """워커 상태 열거형."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class WorkerConfig(BaseModel):
    """워커 설정 모델이다."""

    name: str = Field(default="worker")
    poll_timeout: Optional[float] = Field(default=1.0, ge=0)
    max_retries: int = Field(default=0, ge=0)
    stop_on_error: bool = Field(default=False)
