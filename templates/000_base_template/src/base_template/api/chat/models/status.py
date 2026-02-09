"""
목적: Chat 태스크 상태 API 모델을 정의한다.
설명: task_id 기반 상태 조회 응답 모델을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/api/chat/services/task_manager.py
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TaskStatus(str, Enum):
    """Chat 비동기 태스크 상태."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    STREAMING = "STREAMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskStatusResponse(BaseModel):
    """태스크 상태 조회 응답 모델."""

    session_id: str
    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
