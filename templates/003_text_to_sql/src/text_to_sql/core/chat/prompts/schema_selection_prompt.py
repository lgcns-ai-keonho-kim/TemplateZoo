"""
목적: 스키마 선택 단계용 LLM 프롬프트를 정의한다.
설명: 사용자 질의와 alias별 스키마 요약을 바탕으로 사용할 target alias 목록을 쉼표 구분 문자열로 반환하게 한다.
디자인 패턴: 모듈 싱글턴
참조: src/text_to_sql/core/chat/nodes/schema_selection_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_SCHEMA_SELECTION_PROMPT = textwrap.dedent(
    """
    당신은 Text-to-SQL 시스템의 스키마 선택기입니다.

    작업:
    - 아래 alias 목록과 스키마 요약을 보고, 현재 질문을 답하는 데 필요한 target alias만 고르세요.
    - 출력 형식은 반드시 쉼표로 구분된 alias 문자열 하나만 반환하세요.
    - 예시: ecommerce 또는 housing,population

    규칙:
    - 반드시 schema_selection_context 안에 있는 alias 이름만 사용하세요.
    - 설명, 이유, JSON, 마크다운 코드블록을 출력하지 마세요.
    - 필요한 alias가 없으면 빈 문자열을 반환하세요.
    - 여러 alias가 필요하면 쉼표로만 구분하세요.
    - 지원 대상은 SQL alias뿐입니다.

    <입력>
      <사용자질의>{user_message}</사용자질의>
      <스키마선택컨텍스트>{schema_selection_context}</스키마선택컨텍스트>
    </입력>
    """
).strip()

SCHEMA_SELECTION_PROMPT = PromptTemplate.from_template(_SCHEMA_SELECTION_PROMPT)

__all__ = ["SCHEMA_SELECTION_PROMPT"]
