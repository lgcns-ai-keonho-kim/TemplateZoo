"""
목적: Chat 프롬프트 공개 API를 제공한다.
설명: 기본 시스템 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/chat/prompts/system_prompt.py
"""

from base_template.core.chat.prompts.system_prompt import SYSTEM_PROMPT

__all__ = [
    "SYSTEM_PROMPT",
]
