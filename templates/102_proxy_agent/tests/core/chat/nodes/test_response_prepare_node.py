"""
목적: response_prepare 노드의 부분 성공 입력 구성을 검증한다.
설명: optional 실패만 응답 경고에 포함되고 required 실패는 정상 응답 요약에 섞이지 않는지 확인한다.
디자인 패턴: 단위 테스트
참조: src/tool_proxy_agent/core/chat/nodes/response_prepare_node.py
"""

from __future__ import annotations

from tool_proxy_agent.core.chat.nodes.response_prepare_node import response_prepare_node


def test_response_prepare_uses_only_optional_failures_for_warning_summary() -> None:
    """부분 성공 응답은 optional 실패만 경고 요약에 포함해야 한다."""

    result = response_prepare_node.run(
        {
            "completed_tool_results": [
                {
                    "tool_call_id": "tool-call-1",
                    "tool_name": "sum_tool",
                    "required": False,
                    "output": {"value": 3},
                }
            ],
            "unresolved_optional_failures": [
                {
                    "tool_call_id": "tool-call-2",
                    "tool_name": "weather_tool",
                    "required": False,
                    "error_code": "TOOL_TIMEOUT",
                    "error": "timeout",
                }
            ],
            "unresolved_required_failures": [
                {
                    "tool_call_id": "tool-call-3",
                    "tool_name": "db_tool",
                    "required": True,
                    "error_code": "TOOL_RETRY_EXHAUSTED",
                    "error": "db unavailable",
                }
            ],
        }
    )

    assert "sum_tool" in result["tool_execution_summary"]
    assert "weather_tool" in result["tool_execution_summary"]
    assert "db_tool" not in result["tool_execution_summary"]
    assert "weather_tool" in result["optional_tool_failure_summary"]
    assert "db_tool" not in result["optional_tool_failure_summary"]


def test_response_prepare_returns_empty_warning_text_when_optional_failure_missing() -> None:
    """optional 실패가 없으면 기본 경고 문구를 반환해야 한다."""

    result = response_prepare_node.run(
        {
            "completed_tool_results": [],
            "unresolved_optional_failures": [],
        }
    )

    assert result["optional_tool_failure_summary"] == "부분 성공 경고 없음"
