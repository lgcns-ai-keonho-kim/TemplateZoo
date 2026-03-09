"""
목적: raw SQL 생성 노드의 응답 텍스트 정규화를 검증한다.
설명: 구조화 content와 코드블록 응답이 실제 SQL 문자열로 정규화되는지 확인한다.
디자인 패턴: 노드 단위 테스트
참조: src/text_to_sql/core/chat/nodes/raw_sql_generate_node.py
"""

from __future__ import annotations

from text_to_sql.core.chat.nodes.raw_sql_generate_node import _extract_llm_text


def test_extract_llm_text_flattens_structured_content_list() -> None:
    """list 기반 구조화 content는 text 필드를 이어붙여야 한다."""

    content = [
        {"type": "text", "text": "SELECT 1"},
        {"type": "text", "text": " FROM dual"},
    ]

    result = _extract_llm_text(content)

    assert result == "SELECT 1 FROM dual"


def test_extract_llm_text_reads_text_field_from_mapping() -> None:
    """mapping 기반 content는 text 필드를 읽어야 한다."""

    result = _extract_llm_text({"type": "text", "text": "SELECT * FROM test"})

    assert result == "SELECT * FROM test"
