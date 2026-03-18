"""
목적: Agent 최종 응답 노드 조립체를 제공한다.
설명: 모델/클라이언트/노드를 모듈 레벨에서 선언해 의도별 최종 응답 생성에 사용한다.
디자인 패턴: 모듈 조립
참조: src/single_request_agent/core/agent/graphs/agent_graph.py
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

from single_request_agent.core.agent.prompts import RESPONSE_PROMPT
from single_request_agent.integrations.llm import LLMClient
from single_request_agent.shared.agent.nodes import LLMNode

_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", ""),
    project=os.getenv("GEMINI_PROJECT", ""),
    thinking_level="minimal",
)


# 참고: name은 로깅 구분용 식별자이다.
_llm_client = LLMClient(
    model=_model,
    name="agent-response-llm",
)

response_node = LLMNode(
    llm_client=_llm_client,
    node_name="response",
    prompt=RESPONSE_PROMPT,
    output_key="assistant_message",
)

__all__ = ["response_node"]
