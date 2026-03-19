"""
목적: core chat tool registry 단일 진입점을 제공한다.
설명: ToolRegistry 싱글턴을 선언하고 기본 Tool을 모듈 로드시 즉시 등록한다.
디자인 패턴: 싱글턴 + 모듈 초기화
참조:
- src/tool_proxy_agent/core/chat/tools/math_tools.py
- src/tool_proxy_agent/core/chat/tools/api_get_weather.py
- src/tool_proxy_agent/core/chat/tools/api_agent_response.py
"""

from __future__ import annotations

from tool_proxy_agent.core.chat.tools.api_agent_response import (
    api_agent_response,
)
from tool_proxy_agent.core.chat.tools.math_tools import add_number
from tool_proxy_agent.core.chat.tools.api_get_weather import get_weather
from tool_proxy_agent.shared.chat.tools.registry import ToolRegistry

registry = ToolRegistry()

# `name`: selector가 선택하는 고유 tool 식별자
# `description`: selector 프롬프트에 노출되는 기능 설명
# `args_schema`: selector가 생성해야 할 인자 JSON 스키마
# `fn`: 실제 실행 함수(ToolCall -> ToolResult)
# `required`: 기본 실행 중요도 (False면 step에서만 필수 승격 가능)
# `timeout_seconds`: 단일 시도 최대 실행 시간(초)
# `retry_count`: 실패 시 재시도 횟수 (총 시도 횟수 = retry_count + 1)
# `retry_backoff_seconds`: 재시도 간 대기 시간(초) 튜플
registry.add_tool(
    name="get_weather",
    description="날씨 API를 GET으로 조회한다. 현재는 고정 응답을 반환한다.",
    args_schema={
        # 전체 인자 payload는 JSON object 여야 한다.
        "type": "object",
        "properties": {
            # 지역명(예: "Seoul")
            "region": {"type": "string"},
        },
        # 필수 인자: region
        "required": ["region"],
        # 정의되지 않은 추가 인자는 허용하지 않는다.
        "additionalProperties": False,
    },
    fn=get_weather,
    required=False,
    timeout_seconds=30.0,
    retry_count=2,
    retry_backoff_seconds=(0.5, 1.0),
)

# `name`: selector가 선택하는 고유 tool 식별자
# `description`: selector 프롬프트에 노출되는 기능 설명
# `args_schema`: selector가 생성해야 할 인자 JSON 스키마
# `fn`: 실제 실행 함수(ToolCall -> ToolResult)
# `required`: 기본 실행 중요도 (False면 step에서만 필수 승격 가능)
# `timeout_seconds`: 단일 시도 최대 실행 시간(초)
# `retry_count`: 실패 시 재시도 횟수 (총 시도 횟수 = retry_count + 1)
# `retry_backoff_seconds`: 재시도 간 대기 시간(초) 튜플
registry.add_tool(
    name="add_number",
    description="두 정수 a, b를 더한다.",
    args_schema={
        # 전체 인자 payload는 JSON object 여야 한다.
        "type": "object",
        "properties": {
            # 첫 번째 피연산자
            "a": {"type": "integer"},
            # 두 번째 피연산자
            "b": {"type": "integer"},
        },
        # 필수 인자: a, b
        "required": ["a", "b"],
        # 정의되지 않은 추가 인자는 허용하지 않는다.
        "additionalProperties": False,
    },
    fn=add_number,
    required=False,
    timeout_seconds=30.0,
    retry_count=2,
    retry_backoff_seconds=(0.5, 1.0),
)

# `name`: selector가 선택하는 고유 tool 식별자
# `description`: selector 프롬프트에 노출되는 기능 설명
# `args_schema`: selector가 생성해야 할 인자 JSON 스키마
# `fn`: 실제 실행 함수(ToolCall -> ToolResult)
# `required`: 기본 실행 중요도 (False면 step에서만 필수 승격 가능)
# `timeout_seconds`: 단일 시도 최대 실행 시간(초)
# `retry_count`: 실패 시 재시도 횟수 (총 시도 횟수 = retry_count + 1)
# `retry_backoff_seconds`: 재시도 간 대기 시간(초) 튜플
registry.add_tool(
    name="api_agent_response",
    description="내부 Agent API에 /chat을 제출하고 /events SSE를 소비하는 흐름 예시를 제공한다.",
    args_schema={
        # 전체 인자 payload는 JSON object 여야 한다.
        "type": "object",
        "properties": {
            # 사용자 질문 본문
            "message": {"type": "string"},
            # 대상 API base URL (예: http://127.0.0.1:8000)
            "base_url": {"type": "string"},
            # 기존 세션 이어쓰기용 session_id (없으면 신규 세션)
            "session_id": {"type": "string"},
            # /chat 제출 시 전달할 context_window
            "context_window": {"type": "integer"},
            # 네트워크 연결 타임아웃(초)
            "connect_timeout_seconds": {"type": "number"},
            # SSE 읽기 타임아웃(초)
            "read_timeout_seconds": {"type": "number"},
        },
        # 필수 인자: message
        "required": ["message"],
        # 정의되지 않은 추가 인자는 허용하지 않는다.
        "additionalProperties": False,
    },
    fn=api_agent_response,
    required=False,
    timeout_seconds=30.0,
    retry_count=2,
    retry_backoff_seconds=(0.5, 1.0),
)

__all__ = ["registry"]
