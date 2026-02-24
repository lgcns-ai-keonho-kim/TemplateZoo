"""
목적: 로깅에 필요한 공통 모델을 정의한다.
설명: 로그 레벨, 컨텍스트, 레코드 구조를 Pydantic으로 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/rag_chatbot/shared/logging/logger.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """로그 레벨 열거형."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogContext(BaseModel):
    """로그 컨텍스트 모델이다.

    Args:
        trace_id: 트레이스 식별자.
        span_id: 스팬 식별자.
        request_id: 요청 식별자.
        user_id: 사용자 식별자.
        tags: 자유형 태그.
    """

    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)


def _utc_now() -> datetime:
    """UTC 기준의 timezone-aware 시간을 반환한다."""

    return datetime.now(timezone.utc)


class LogRecord(BaseModel):
    """로그 레코드 모델이다.

    Args:
        level: 로그 레벨.
        message: 로그 메시지.
        timestamp: 기록 시각.
        logger_name: 로거 이름.
        context: 로그 컨텍스트.
        metadata: 추가 메타데이터.
    """

    level: LogLevel
    message: str
    timestamp: datetime = Field(default_factory=_utc_now)
    logger_name: str
    context: Optional[LogContext] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
