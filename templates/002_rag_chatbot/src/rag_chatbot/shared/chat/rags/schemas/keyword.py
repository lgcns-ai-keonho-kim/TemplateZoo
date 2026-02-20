"""
목적: 키워드 생성 출력 파서를 제공한다.
설명: comma-separated 문자열을 안전하게 키워드 리스트로 변환한다.
디자인 패턴: 파서 함수
참조: src/rag_chatbot/shared/chat/rags/functions/query_keyword_expander.py
"""

from __future__ import annotations


def parse_keywords(raw: str, max_items: int) -> list[str]:
    """comma-separated 키워드를 파싱한다."""

    if max_items <= 0:
        return []
    text = str(raw or "").strip()
    if not text:
        return []

    normalized = text.replace("\n", ",")
    candidates = [item.strip() for item in normalized.split(",") if item.strip()]

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        lowered = candidate.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(candidate)
        if len(deduped) >= max_items:
            break
    return deduped


__all__ = ["parse_keywords"]
