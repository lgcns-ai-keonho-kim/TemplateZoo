"""
목적: Agent 코어 상수 공개 API를 제공한다.
설명: safeguard 메시지 상수를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/one_shot_tool_calling_agent/core/agent/const/messages/__init__.py
"""

from one_shot_tool_calling_agent.core.agent.const.messages import SafeguardRejectionMessage

__all__ = [
    "SafeguardRejectionMessage",
]
