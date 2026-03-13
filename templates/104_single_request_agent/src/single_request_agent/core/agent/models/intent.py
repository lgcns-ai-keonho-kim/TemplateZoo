"""
목적: 단일 요청 Agent의 사용자 의도 타입을 정의한다.
설명: 요약, 번역, 형식 기반 글쓰기, 일반 응답 의도를 표준 토큰으로 정규화한다.
디자인 패턴: 값 객체(Value Object)
참조: src/single_request_agent/core/agent/nodes/intent_prepare_node.py
"""

from __future__ import annotations

from enum import Enum


class AgentIntentType(str, Enum):
    """단일 요청 Agent가 지원하는 의도 타입."""

    SUMMARY = "SUMMARY"
    TRANSLATION = "TRANSLATION"
    FORMAT_WRITING = "FORMAT_WRITING"
    GENERAL = "GENERAL"

    @classmethod
    def from_raw(cls, raw_value: object) -> "AgentIntentType":
        """분류기 원문을 표준 의도 토큰으로 정규화한다."""

        normalized = str(raw_value or "").strip().upper().replace("-", "_")
        alias_map = {
            "SUMMARIZE": cls.SUMMARY,
            "SUMMARY": cls.SUMMARY,
            "SUM": cls.SUMMARY,
            "TRANSLATE": cls.TRANSLATION,
            "TRANSLATION": cls.TRANSLATION,
            "TRANSLATOR": cls.TRANSLATION,
            "FORMAT_WRITING": cls.FORMAT_WRITING,
            "FORMATTED_WRITING": cls.FORMAT_WRITING,
            "WRITE_FORMAT": cls.FORMAT_WRITING,
            "WRITING": cls.FORMAT_WRITING,
            "GENERAL": cls.GENERAL,
            "CHAT": cls.GENERAL,
            "QNA": cls.GENERAL,
            "QUESTION": cls.GENERAL,
        }
        if normalized in alias_map:
            return alias_map[normalized]
        for candidate in cls:
            if normalized.startswith(candidate.value):
                return candidate
        return cls.GENERAL


__all__ = ["AgentIntentType"]
