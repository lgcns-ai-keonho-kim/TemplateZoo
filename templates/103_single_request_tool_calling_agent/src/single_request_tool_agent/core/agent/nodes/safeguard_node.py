"""
목적: LLM 기반 safeguard 노드 조립체를 제공한다.
설명: shared LLMNode를 사용해 사용자 입력을 PASS 또는 차단 라벨(PII/HARMFUL/PROMPT_INJECTION)로 판정한다.
디자인 패턴: 모듈 조립
참조: src/single_request_tool_agent/core/agent/graphs/chat_graph.py
"""

from __future__ import annotations
import os
from langchain_google_genai import ChatGoogleGenerativeAI

from single_request_tool_agent.core.agent.prompts import SAFEGUARD_PROMPT
from single_request_tool_agent.integrations.llm import LLMClient
from single_request_tool_agent.shared.agent.nodes import LLMNode


_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", ""),
    project=os.getenv("GEMINI_PROJECT", ""),
    thinking_level="minimal",
)


# 참고: name은 로깅에서 safeguard 전용 호출을 식별하기 위한 값이다.
_llm_client = LLMClient(
    model=_model,
    name="chat-safeguard-llm",
)

# 참고:
safeguard_node = LLMNode(
    llm_client=_llm_client,
    node_name="safeguard",  # 스트림 이벤트의 node 필드 값
    prompt=SAFEGUARD_PROMPT,  # 답변 정책/역할을 정의하는 프롬프트 템플릿
    output_key="safeguard_result",  # PASS/PII/HARMFUL/PROMPT_INJECTION 결과를 state에 기록
    history_key="__skip_history__",  # state에 존재하지 않는 키를 지정해 히스토리를 비활성화 (즉, 현재 user_message 한 건만 분류)
    stream_tokens=False,
)

__all__ = ["safeguard_node"]
