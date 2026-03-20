"""
목적: DB 필터 연산자 열거형을 제공한다.
설명: 동등/범위/집합/포함 기반 비교 연산자를 정의한다.
디자인 패턴: 열거형
참조: src/one_shot_tool_calling_agent/integrations/db/base/models.py
"""

from __future__ import annotations

from enum import Enum


class FilterOperator(str, Enum):
    """필터 연산자."""

    EQ = "EQ"
    NE = "NE"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"
