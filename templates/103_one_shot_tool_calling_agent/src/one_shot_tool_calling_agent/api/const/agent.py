"""
목적: Agent API 라우팅 상수를 정의한다.
설명: one shot tool calling agent 실행 경로의 prefix, tag, path 상수를 중앙에서 관리한다.
디자인 패턴: 상수 객체 패턴
참조: src/one_shot_tool_calling_agent/api/agent/routers/router.py
"""

from __future__ import annotations

AGENT_API_PREFIX = "/agent"
AGENT_API_TAG = "agent"
AGENT_API_RUN_PATH = ""
