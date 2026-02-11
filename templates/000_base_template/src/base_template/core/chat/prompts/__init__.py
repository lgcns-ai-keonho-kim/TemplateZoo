"""
목적: Chat 프롬프트 공개 API를 제공한다.
설명: 기본 답변 프롬프트와 안전성 분류 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/core/chat/prompts/system_prompt.py, src/base_template/core/chat/prompts/safeguard_prompt.py
"""

from base_template.core.chat.prompts.safeguard_prompt import SAFEGUARD_PROMPT
from base_template.core.chat.prompts.system_prompt import CHAT_PROMPT

__all__ = [
    "SAFEGUARD_PROMPT",
    "CHAT_PROMPT",
]
