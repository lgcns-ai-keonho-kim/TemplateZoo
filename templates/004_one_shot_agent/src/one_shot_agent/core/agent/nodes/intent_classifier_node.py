"""
목적: 사용자 의도 분류 LLM 노드 조립체를 제공한다.
설명: shared LLMNode를 사용해 사용자 요청을 표준 의도 토큰으로 분류한다.
디자인 패턴: 모듈 조립
참조: src/one_shot_agent/core/agent/prompts/intent_classifier_prompt.py
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

from one_shot_agent.core.agent.prompts import (
    INTENT_CLASSIFIER_PROMPT,
)
from one_shot_agent.integrations.llm import LLMClient
from one_shot_agent.shared.agent.nodes import LLMNode

_model = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", ""),
    project=os.getenv("GEMINI_PROJECT", ""),
    thinking_level="minimal",
)

_llm_client = LLMClient(
    model=_model,
    name="intent-classifier-llm",
)

intent_classifier_node = LLMNode(
    llm_client=_llm_client,
    node_name="intent_classify",
    prompt=INTENT_CLASSIFIER_PROMPT,
    output_key="intent_type_raw",
    history_key="__skip_history__",
    stream_tokens=False,
)

__all__ = ["intent_classifier_node"]
