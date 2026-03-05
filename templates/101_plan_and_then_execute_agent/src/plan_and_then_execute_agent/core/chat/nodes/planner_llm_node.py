"""
목적: Planner LLM 노드 조립체를 제공한다.
설명: 사용자 질의와 Tool 스펙을 기반으로 실행 계획(JSON) 원문을 생성한다.
디자인 패턴: 모듈 조립
참조: src/plan_and_then_execute_agent/shared/chat/nodes/llm_node.py
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

from plan_and_then_execute_agent.core.chat.prompts import PLANNER_PROMPT
from plan_and_then_execute_agent.integrations.llm import LLMClient
from plan_and_then_execute_agent.shared.chat.nodes import LLMNode
from plan_and_then_execute_agent.shared.logging import Logger, create_default_logger

_planner_llm_logger: Logger = create_default_logger("PlannerLLMNode")
_planner_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", ""),
    project=os.getenv("GEMINI_PROJECT", ""),
    thinking_level="minimal",
)
_planner_llm_client = LLMClient(
    model=_planner_model,
    name="chat-planner-llm",
)

planner_llm_node = LLMNode(
    llm_client=_planner_llm_client,
    node_name="planner_llm",
    prompt=PLANNER_PROMPT,
    output_key="plan_raw",
    history_key="__skip_history__",
    stream_tokens=False,
    logger=_planner_llm_logger,
)

__all__ = ["planner_llm_node"]
