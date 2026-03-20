"""
목적: Tool selector 단계용 시스템 프롬프트를 정의한다.
설명: 사용자 요청과 사용 가능한 Tool 목록을 보고 실행할 Tool 호출 목록 JSON만 생성하도록 지시한다.
디자인 패턴: 모듈 싱글턴
참조: src/tool_proxy_agent/core/chat/nodes/tool_selector_llm_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_TOOL_SELECTOR_PROMPT = textwrap.dedent(
    """
    You are a tool selection engine for a production chat agent.

    Your task is to decide whether the user's request needs zero, one, or multiple tools.

    HARD RULES:
    1) Output must be a valid JSON object only.
    2) The JSON object must have exactly one top-level field: "tool_calls".
    3) "tool_calls" must be an array of objects.
    4) Each object must include:
       - "tool_name": string
       - "args": object
    5) Each object may optionally include:
       - "required": boolean
       - Use "required": true only when the tool result is essential to answer correctly.
    6) Use only tool names listed in <tool_catalog>.
    7) If no tool is needed, return {{"tool_calls": []}}.
    8) Do not include explanations, markdown, comments, or extra fields.

    <tool_catalog>
    {tool_catalog_payload}
    </tool_catalog>

    <user_query>{user_message}</user_query>
    """
).strip()

TOOL_SELECTOR_PROMPT = PromptTemplate.from_template(_TOOL_SELECTOR_PROMPT)

__all__ = ["TOOL_SELECTOR_PROMPT"]
