"""
목적: Chat 프롬프트 공개 API를 제공한다.
설명: 현재 축소형 tool selector 그래프에서 사용하는 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/tool_proxy_agent/core/chat/prompts/chat_prompt.py, src/tool_proxy_agent/core/chat/prompts/safeguard_prompt.py
"""

from tool_proxy_agent.core.chat.prompts.chat_prompt import CHAT_PROMPT
from tool_proxy_agent.core.chat.prompts.retry_prompt import RETRY_PROMPT
from tool_proxy_agent.core.chat.prompts.safeguard_prompt import (
    SAFEGUARD_PROMPT,
)
from tool_proxy_agent.core.chat.prompts.tool_selector_prompt import (
    TOOL_SELECTOR_PROMPT,
)

__all__ = [
    "SAFEGUARD_PROMPT",
    "CHAT_PROMPT",
    "TOOL_SELECTOR_PROMPT",
    "RETRY_PROMPT",
]
