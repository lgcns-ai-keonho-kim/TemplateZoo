"""
목적: Replan 단계용 시스템 프롬프트를 정의한다.
설명: 실패 step 정보를 반영해 수정된 실행 계획(JSON)을 재생성하도록 지시한다.
디자인 패턴: 모듈 싱글턴
참조: src/plan_and_then_execute_agent/core/chat/nodes/replan_llm_node.py
"""

from __future__ import annotations

import textwrap

from langchain_core.prompts import PromptTemplate

_REPLAN_PROMPT = textwrap.dedent(
    """
    You are a replanning engine for a production plan-and-then-execute agent.

    You will receive:
    - original user query
    - previous failed plan summary
    - failure summary
    - available tools

    Produce a corrected strict JSON plan.

    HARD RULES:
    1) Output valid JSON object only (no markdown).
    2) Use only tool names listed in <tools_payload>.
    3) Ensure dependency graph is acyclic.
    4) Keep plan practical and minimal.

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
    <previous_plan>{replan_previous_plan_summary}</previous_plan>
    <failure_summary>{replan_failure_summary}</failure_summary>
    <tools_payload>{planner_tools_payload}</tools_payload>
    """
).strip()

REPLAN_PROMPT = PromptTemplate.from_template(_REPLAN_PROMPT)

__all__ = ["REPLAN_PROMPT"]
