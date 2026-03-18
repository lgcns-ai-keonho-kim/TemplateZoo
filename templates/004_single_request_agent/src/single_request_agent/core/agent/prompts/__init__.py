"""
목적: Agent 프롬프트 공개 API를 제공한다.
설명: 의도 분류 기반 단일 요청 그래프에서 사용하는 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/single_request_agent/core/agent/prompts/response_prompt.py, src/single_request_agent/core/agent/prompts/intent_classifier_prompt.py
"""

from single_request_agent.core.agent.prompts.intent_classifier_prompt import (
    INTENT_CLASSIFIER_PROMPT,
)
from single_request_agent.core.agent.prompts.response_prompt import RESPONSE_PROMPT
from single_request_agent.core.agent.prompts.safeguard_prompt import (
    SAFEGUARD_PROMPT,
)

__all__ = [
    "RESPONSE_PROMPT",
    "INTENT_CLASSIFIER_PROMPT",
    "SAFEGUARD_PROMPT",
]
