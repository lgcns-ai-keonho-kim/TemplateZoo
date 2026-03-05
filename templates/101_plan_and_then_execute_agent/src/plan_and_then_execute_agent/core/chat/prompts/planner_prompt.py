"""
목적: Plan 단계용 시스템 프롬프트를 정의한다.
설명: 사용자 질의를 실행 가능한 단계(JSON steps[])로 변환하도록 지시한다.
디자인 패턴: 모듈 싱글턴
참조: src/plan_and_then_execute_agent/core/chat/nodes/planner_llm_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_PLANNER_PROMPT = textwrap.dedent(
    """
    You are a planning engine for a production plan-and-then-execute agent.

    Your task is to produce a strict JSON execution plan.

    HARD RULES:
    1) Output must be valid JSON object only (no markdown, no explanation).
    2) Use only tool names listed in <tools_payload>.
    3) Every step must include: id, goal, tool_name, args, depends_on.
    4) depends_on must reference existing step ids only.
    5) Keep args minimal and executable.

    JSON schema (conceptual):
    {{
      "plan_id": "string",
      "steps": [
        {{
          "id": "string",
          "goal": "string",
          "tool_name": "string",
          "args": {{"key": "value"}},
          "depends_on": ["step_id"]
        }}
      ]
    }}

    <user_query>{user_message}</user_query>
    <history_summary>{planner_history_summary}</history_summary>
    <tools_payload>{planner_tools_payload}</tools_payload>
    """
).strip()

PLANNER_PROMPT = PromptTemplate.from_template(_PLANNER_PROMPT)

__all__ = ["PLANNER_PROMPT"]
