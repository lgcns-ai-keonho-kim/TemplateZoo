"""
목적: 관련성 필터 출력 파서를 제공한다.
설명: LLM 문자열 출력에서 선택된 문서 index 집합을 추출한다.
디자인 패턴: 파서 함수
참조: src/rag_chatbot/shared/chat/rags/functions/relevance_filter.py
"""

from __future__ import annotations

import re


_INDEX_PATTERN = re.compile(r"\d+")


def parse_relevance_indexes(raw: str, max_index: int) -> list[int]:
    """문자열에서 index 목록을 추출한다."""

    if max_index <= 0:
        return []
    text = str(raw or "").strip()
    if not text:
        return []

    extracted = _INDEX_PATTERN.findall(text)
    if not extracted:
        return []

    deduped: list[int] = []
    seen: set[int] = set()
    for token in extracted:
        value = int(token)
        if value < 0 or value >= max_index:
            continue
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


__all__ = ["parse_relevance_indexes"]
