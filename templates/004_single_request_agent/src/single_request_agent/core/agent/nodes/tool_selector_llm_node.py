"""
목적: Tool selector LLM 노드 조립체를 제공한다.
설명: shared LLMNode를 사용해 Tool 호출 목록 JSON을 생성한다.
디자인 패턴: 모듈 조립
참조: src/single_request_agent/core/agent/prompts/tool_selector_prompt.py
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

from single_request_agent.core.agent.prompts import TOOL_SELECTOR_PROMPT
from single_request_agent.integrations.llm import LLMClient
from single_request_agent.shared.agent.nodes import LLMNode

_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", ""),
    project=os.getenv("GEMINI_PROJECT", ""),
    thinking_level="minimal",
)

_llm_client = LLMClient(
    model=_model,
    name="tool-selector-llm",
)

tool_selector_llm_node = LLMNode(
    llm_client=_llm_client,
    node_name="tool_selector",
    prompt=TOOL_SELECTOR_PROMPT,
    output_key="tool_selection_raw",
    stream_tokens=False,
)

__all__ = ["tool_selector_llm_node"]
