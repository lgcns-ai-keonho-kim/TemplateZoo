"""
목적: core agent tool registry 단일 진입점을 제공한다.
설명: ToolRegistry 싱글턴을 선언하고 기본 Tool을 모듈 로드시 즉시 등록한다.
디자인 패턴: 싱글턴 + 모듈 초기화
참조:
- src/single_request_agent/core/agent/tools/math_tools.py
- src/single_request_agent/core/agent/tools/api_get_weather.py
- src/single_request_agent/core/agent/tools/draft_email.py
"""

from __future__ import annotations

from single_request_agent.core.agent.tools.draft_email import draft_email
from single_request_agent.core.agent.tools.math_tools import add_number
from single_request_agent.core.agent.tools.api_get_weather import get_weather
from single_request_agent.shared.agent.tools.registry import ToolRegistry

registry = ToolRegistry()

# `name`: selector가 선택하는 고유 tool 식별자
# `description`: selector 프롬프트에 노출되는 기능 설명
# `args_schema`: selector가 생성해야 할 인자 JSON 스키마
# `fn`: 실제 실행 함수(ToolCall -> ToolResult)
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
    timeout_seconds=30.0,
    retry_count=2,
    retry_backoff_seconds=(0.5, 1.0),
)

# `name`: selector가 선택하는 고유 tool 식별자
# `description`: selector 프롬프트에 노출되는 기능 설명
# `args_schema`: selector가 생성해야 할 인자 JSON 스키마
# `fn`: 실제 실행 함수(ToolCall -> ToolResult)
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
    timeout_seconds=30.0,
    retry_count=2,
    retry_backoff_seconds=(0.5, 1.0),
)

# `name`: selector가 선택하는 고유 tool 식별자
# `description`: selector 프롬프트에 노출되는 기능 설명
# `args_schema`: selector가 생성해야 할 인자 JSON 스키마
# `fn`: 실제 실행 함수(ToolCall -> ToolResult)
# `timeout_seconds`: 단일 시도 최대 실행 시간(초)
# `retry_count`: 실패 시 재시도 횟수 (총 시도 횟수 = retry_count + 1)
# `retry_backoff_seconds`: 재시도 간 대기 시간(초) 튜플
registry.add_tool(
    name="draft_email",
    description="수신자, 제목, 목적을 바탕으로 이메일 초안을 생성한다. 현재는 mock 초안을 반환한다.",
    args_schema={
        "type": "object",
        "properties": {
            "recipient": {"type": "string"},
            "subject": {"type": "string"},
            "purpose": {"type": "string"},
            "tone": {"type": "string"},
        },
        "required": ["recipient", "subject", "purpose"],
        "additionalProperties": False,
    },
    fn=draft_email,
    timeout_seconds=30.0,
    retry_count=2,
    retry_backoff_seconds=(0.5, 1.0),
)

__all__ = ["registry"]
