"""
목적: Tool retry selector LLM 노드 조립체를 제공한다.
설명: shared LLMNode를 사용해 실패한 Tool 호출의 대체 JSON을 생성한다.
디자인 패턴: 모듈 조립
참조: src/one_shot_tool_calling_agent/core/agent/prompts/retry_prompt.py
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

from one_shot_tool_calling_agent.core.agent.prompts import RETRY_PROMPT
from one_shot_tool_calling_agent.integrations.llm import LLMClient
from one_shot_tool_calling_agent.shared.agent.nodes import LLMNode

_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", ""),
    project=os.getenv("GEMINI_PROJECT", ""),
    thinking_level="minimal",
)

_llm_client = LLMClient(
    model=_model,
    name="tool-retry-llm",
)

retry_llm_node = LLMNode(
    llm_client=_llm_client,
    node_name="retry_selector",
    prompt=RETRY_PROMPT,
    output_key="retry_selection_raw",
    stream_tokens=False,
)

__all__ = ["retry_llm_node"]
