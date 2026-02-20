"""
목적: 이진 관련성(0/1) 파서를 제공한다.
설명: LLM 문자열 출력에서 0 또는 1 판정값을 안정적으로 추출한다.
디자인 패턴: 파서 함수
참조: src/rag_chatbot/shared/chat/rags/functions/binary_relevance_filter.py
"""

from __future__ import annotations

import re

_BINARY_PATTERN = re.compile(r"\b([01])\b")


def parse_binary_relevance(raw: str) -> int:
    """LLM 출력에서 이진 관련성 값(0/1)을 반환한다."""

    text = str(raw or "").strip()
    if not text:
        return 0
    if text == "1":
        return 1
    if text == "0":
        return 0

    matched = _BINARY_PATTERN.search(text)
    if matched is not None:
        return int(matched.group(1))

    if text.startswith("1"):
        return 1
    if text.startswith("0"):
        return 0
    return 0


__all__ = ["parse_binary_relevance"]
