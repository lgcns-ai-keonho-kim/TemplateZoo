"""
목적: DB 정렬 순서 열거형을 제공한다.
설명: 오름차순/내림차순 정렬 옵션을 정의한다.
디자인 패턴: 열거형
참조: src/one_shot_tool_calling_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from enum import Enum


class SortOrder(str, Enum):
    """정렬 순서."""

    ASC = "ASC"
    DESC = "DESC"
