"""
목적: Replan LLM 노드 조립체를 제공한다.
설명: 실패 요약을 반영해 수정 계획(JSON) 원문을 생성한다.
디자인 패턴: 모듈 조립
참조: src/plan_and_then_execute_agent/shared/chat/nodes/llm_node.py
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

from plan_and_then_execute_agent.core.chat.prompts import REPLAN_PROMPT
from plan_and_then_execute_agent.integrations.llm import LLMClient
from plan_and_then_execute_agent.shared.chat.nodes import LLMNode
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_replan_llm_logger: Logger = create_default_logger("ReplanLLMNode")
_replan_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", ""),
    project=os.getenv("GEMINI_PROJECT", ""),
    thinking_level="minimal",
)
_replan_llm_client = LLMClient(
    model=_replan_model,
    name="chat-replan-llm",
)

replan_llm_node = LLMNode(
    llm_client=_replan_llm_client,
    node_name="replan_llm",
    prompt=REPLAN_PROMPT,
    output_key="replan_raw",
    history_key="__skip_history__",
    stream_tokens=False,
    logger=_replan_llm_logger,
)

__all__ = ["replan_llm_node"]
