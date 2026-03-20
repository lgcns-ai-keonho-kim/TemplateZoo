"""
목적: Safeguard 차단 메시지 노드 조립체를 제공한다.
설명: safeguard_result 값을 SafeguardRejectionMessage Enum 문구로 변환해 assistant_message로 기록한다.
디자인 패턴: 모듈 조립
참조: src/one_shot_tool_calling_agent/core/agent/graphs/agent_graph.py
"""

from __future__ import annotations

from one_shot_tool_calling_agent.core.agent.const.messages import (
    SafeguardRejectionMessage,
)
from one_shot_tool_calling_agent.shared.agent.nodes import MessageNode

# 참고:
# - selector_key: safeguard 분류 결과(PASS/PII/HARMFUL/PROMPT_INJECTION)
# - output_key: 차단 문구를 assistant_message로 기록해서 내부 이벤트와 최종 응답에서 재사용
# - default_member: 알 수 없는 토큰이 들어와도 안전하게 HARMFUL 문구를 사용
safeguard_message_node = MessageNode(
    messages=SafeguardRejectionMessage,
    selector_key="safeguard_result",
    output_key="assistant_message",
    default_member="HARMFUL",
)

__all__ = ["safeguard_message_node"]
