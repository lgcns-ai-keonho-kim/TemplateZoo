"""
목적: Chat 태스크 결과 API 모델을 정의한다.
설명: task_id 기반 결과 조회 응답 모델을 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/api/chat/services/task_manager.py
"""

from __future__ import annotations

from pydantic import BaseModel

from base_template.api.chat.models.message import MessageResponse
from base_template.api.chat.models.status import TaskStatus


class TaskResultResponse(BaseModel):
    """태스크 결과 조회 응답 모델."""

    session_id: str
    task_id: str
    status: TaskStatus
    assistant_message: MessageResponse | None = None
    error_message: str | None = None
