"""
목적: DB 필드 출처 열거형을 제공한다.
설명: 필드가 컬럼/페이로드 중 어디에서 조회되는지 표현한다.
디자인 패턴: 열거형
참조: src/one_shot_tool_calling_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from enum import Enum


class FieldSource(str, Enum):
    """필드 출처 타입."""

    AUTO = "AUTO"
    COLUMN = "COLUMN"
    PAYLOAD = "PAYLOAD"
