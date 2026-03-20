"""
목적: Agent 프롬프트 공개 API를 제공한다.
설명: 현재 축소형 tool selector 그래프에서 사용하는 프롬프트를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_tool_calling_agent/core/agent/prompts/agent_prompt.py, src/one_shot_tool_calling_agent/core/agent/prompts/safeguard_prompt.py
"""

from one_shot_tool_calling_agent.core.agent.prompts.agent_prompt import AGENT_PROMPT
from one_shot_tool_calling_agent.core.agent.prompts.retry_prompt import RETRY_PROMPT
from one_shot_tool_calling_agent.core.agent.prompts.safeguard_prompt import (
    SAFEGUARD_PROMPT,
)
from one_shot_tool_calling_agent.core.agent.prompts.tool_selector_prompt import (
    TOOL_SELECTOR_PROMPT,
)

__all__ = [
    "SAFEGUARD_PROMPT",
    "AGENT_PROMPT",
    "TOOL_SELECTOR_PROMPT",
    "RETRY_PROMPT",
]
