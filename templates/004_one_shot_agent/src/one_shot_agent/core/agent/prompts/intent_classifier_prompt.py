"""
목적: 사용자 의도 분류용 시스템 프롬프트를 정의한다.
설명: 입력을 요약, 번역, 형식 기반 글쓰기, 일반 응답 중 하나로 분류한다.
디자인 패턴: 모듈 싱글턴
참조: src/one_shot_agent/core/agent/nodes/intent_classifier_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_INTENT_CLASSIFIER_PROMPT = textwrap.dedent(
    """
    당신은 단일 요청 Agent의 의도 분류기입니다.

    입력:
    - user_message: {user_message}

    출력 규칙:
    1) 아래 토큰 중 정확히 하나만 출력합니다.
       SUMMARY
       TRANSLATION
       FORMAT_WRITING
       GENERAL
    2) 설명, 마크다운, 따옴표, 추가 문장을 절대 출력하지 않습니다.
    3) 요약 요청이면 SUMMARY를 선택합니다.
    4) 번역 요청이면 TRANSLATION을 선택합니다.
    5) 메일, 보고서, 공지, 소개글, 표준 형식 문장 작성 요청이면 FORMAT_WRITING을 선택합니다.
    6) 그 외 질문, 설명, 일반 대화성 요청은 GENERAL을 선택합니다.
    7) 애매하면 GENERAL 대신 가장 가까운 작업형 의도를 고르지 말고 GENERAL을 선택합니다.
    """
).strip()

INTENT_CLASSIFIER_PROMPT = PromptTemplate.from_template(_INTENT_CLASSIFIER_PROMPT)

__all__ = ["INTENT_CLASSIFIER_PROMPT"]
