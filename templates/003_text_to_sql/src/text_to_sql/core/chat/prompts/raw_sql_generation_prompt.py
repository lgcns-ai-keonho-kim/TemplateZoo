"""
목적: raw SQL 생성 단계용 LLM 프롬프트를 정의한다.
설명: 선택된 단일 target alias의 스키마 컨텍스트를 기반으로 실행 가능한 읽기 전용 SQL 한 개를 생성하게 한다.
디자인 패턴: 모듈 싱글턴
참조: src/text_to_sql/core/chat/nodes/raw_sql_generate_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_RAW_SQL_GENERATION_PROMPT = textwrap.dedent(
    """
    당신은 Text-to-SQL 시스템의 SQL 작성기입니다.

    작업:
    - 아래 단일 target alias의 스키마만 사용해, 사용자 질문을 답할 수 있는 SQL 한 개를 작성하세요.
    - 출력은 반드시 순수 SQL 문자열만 반환하세요.
    - 설명, 주석, JSON, 코드블록은 금지합니다.

    필수 규칙:
    - 단일 SQL 문만 작성하세요.
    - SELECT 또는 WITH ... SELECT 형태만 허용됩니다.
    - INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, MERGE, CALL, PRAGMA는 금지합니다.
    - 아래 스키마 컨텍스트에 있는 정확한 테이블명/컬럼명만 사용하세요.
    - PostgreSQL에서는 quoted_table_name과 quoted 컬럼 값을 우선 사용하세요.
    - PostgreSQL에서 대문자 식별자나 특수문자가 포함된 테이블/컬럼은 반드시 큰따옴표를 포함한 quoted 값을 그대로 사용하세요.
    - 필요한 경우 alias 내부에서는 JOIN을 사용해도 됩니다.
    - 사용자 질문을 만족하는 데 필요 없는 컬럼은 선택하지 마세요.
    - 정렬과 LIMIT가 필요한 질의면 명시적으로 포함하세요.
    - 질문이 집계를 요구하면 SQL 안에서 직접 집계하세요.
    - 이전 실행 오류가 있으면 그 오류를 직접 수정한 SQL을 다시 작성하세요.

    <입력>
      <사용자질의>{user_message}</사용자질의>
      <target_alias>{target_alias}</target_alias>
      <engine>{target_engine}</engine>
      <스키마컨텍스트>{target_schema_context}</스키마컨텍스트>
      <재시도피드백>{sql_retry_feedback}</재시도피드백>
    </입력>
    """
).strip()

RAW_SQL_GENERATION_PROMPT = PromptTemplate.from_template(_RAW_SQL_GENERATION_PROMPT)

__all__ = ["RAW_SQL_GENERATION_PROMPT"]
