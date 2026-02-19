"""
목적: Safeguard 거부 응답 메시지 Enum을 정의한다.
설명: PII, HARMFUL, PROMPT_INJECTION 유형별 사용자 안내 문구를 제공한다.
디자인 패턴: Enum 상수 객체
참조: src/chatbot/core/chat/nodes/safeguard_node.py
"""

from __future__ import annotations

from enum import Enum


class SafeguardRejectionMessage(str, Enum):
    """Safeguard 차단 유형별 사용자 안내 메시지."""

    PII = "개인정보(PII)가 포함된 요청은 처리할 수 없습니다. 민감정보를 제거한 뒤 다시 요청해 주세요."
    HARMFUL = "유해하거나 위험한 요청으로 판단되어 처리할 수 없습니다."
    PROMPT_INJECTION = "시스템 지침 무력화 시도로 판단되어 요청을 처리할 수 없습니다."
