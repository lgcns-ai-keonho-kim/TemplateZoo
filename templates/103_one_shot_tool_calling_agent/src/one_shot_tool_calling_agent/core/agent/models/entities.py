"""
목적: Agent 도메인 엔티티 모델을 정의한다.
설명: 메시지/역할 타입과 공통 시간 유틸을 Pydantic 기반으로 제공한다.
디자인 패턴: 엔티티 패턴
참조: src/one_shot_tool_calling_agent/shared/agent/nodes/llm_node.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """UTC 기준 timezone-aware 현재 시각을 반환한다."""

    return datetime.now(timezone.utc)


class AgentMessageRole(str, Enum):
    """에이전트 메시지 역할 타입."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentMessage(BaseModel):
    """에이전트 메시지 엔티티."""

    message_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    role: AgentMessageRole
    content: str
    sequence: int = Field(ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
