"""
목적: 날씨 조회 Tool 예시를 제공한다.
설명: 외부 API GET 호출 구조를 가정하되 현재는 고정 응답으로 동작한다.
디자인 패턴: 어댑터
참조: src/single_request_agent/shared/agent/tools/types.py
"""

from __future__ import annotations

from single_request_agent.shared.agent.tools.types import ToolCall, ToolResult

WEATHER_API_URL = "https://example.weather.internal/api/v1/current"


def get_weather(tool_call: ToolCall) -> ToolResult:
    """날씨 조회 API GET 호출을 가정한 Tool 함수."""

    # 참고: 현재 단계에서는 실제 네트워크 호출 없이 고정 응답을 반환한다.
    #
    # 아래는 "단건 GET 요청" 실구현 예시(주석)이다.
    #
    # from typing import Any
    # import requests
    #
    # args: dict[str, Any] = dict(tool_call.get("args") or {})
    # region = str(args.get("region") or "").strip() or "Seoul"
    #
    # try:
    #     response = requests.get(
    #         WEATHER_API_URL,
    #         params={"region": region},
    #         timeout=5,
    #     )
    #     response.raise_for_status()
    #     body = response.json()
    # except requests.RequestException as error:
    #     return {
    #         "ok": False,
    #         "output": {},
    #         "error": f"날씨 API 요청 실패: {error}",
    #     }
    #
    # return {
    #     "ok": True,
    #     "output": {"data": body},
    #     "error": None,
    # }

    # 현재 mock 구현에서는 ToolCall 입력을 사용하지 않으므로 미사용 변수 경고를 방지한다.

    del tool_call

    payload = {
        "country": "South Korea",
        "region": "Seoul",
        "temperature": 14.3,
        "humidity(%)": "55",
    }
    return {
        "ok": True,
        "output": {"data": payload},
        "error": None,
    }
