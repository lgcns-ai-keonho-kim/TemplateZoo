"""
목적: 이진 관련성 파서 함수를 테스트한다.
설명: LLM 출력 문자열에서 0/1 판정값이 안정적으로 추출되는지 검증한다.
디자인 패턴: 단위 테스트
참조: src/rag_chatbot/shared/chat/rags/schemas/binary.py
"""

from __future__ import annotations

import pytest

from rag_chatbot.shared.chat.rags.schemas.binary import parse_binary_relevance


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1", 1),
        ("0", 0),
        ("정답: 1", 1),
        ("결과는 0 입니다", 0),
        ("1\n", 1),
        ("", 0),
        ("판단불가", 0),
    ],
)
def test_parse_binary_relevance(raw: str, expected: int) -> None:
    """문자열 입력이 0/1로 정규화되는지 검증한다."""

    assert parse_binary_relevance(raw) == expected
