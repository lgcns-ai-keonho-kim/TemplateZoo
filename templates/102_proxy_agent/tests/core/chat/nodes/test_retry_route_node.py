"""
목적: retry_route 노드의 실패 승격 정책을 검증한다.
설명: 재시도 한도 전후와 required 실패 존재 여부에 따라 retry/response/error가 올바르게 결정되는지 확인한다.
디자인 패턴: 단위 테스트
참조: src/tool_proxy_agent/core/chat/nodes/retry_route_node.py
"""

from __future__ import annotations

import pytest

from tool_proxy_agent.core.chat.nodes.retry_route_node import retry_route_node
from tool_proxy_agent.shared.exceptions import BaseAppException


def test_retry_route_retries_before_limit() -> None:
    """실패가 있고 재시도 한도 이하면 retry를 반환해야 한다."""

    result = retry_route_node.run(
        {
            "batch_tool_failures": [{"tool_call_id": "tool-call-1"}],
            "retry_count": 0,
            "unresolved_required_failures": [],
        }
    )

    assert result["retry_decision"] == "retry"


def test_retry_route_returns_response_for_optional_failures_after_limit() -> None:
    """optional 실패만 남으면 재시도 한도 초과 뒤에도 response로 진행해야 한다."""

    result = retry_route_node.run(
        {
            "batch_tool_failures": [
                {"tool_call_id": "tool-call-1", "tool_name": "optional_tool"}
            ],
            "retry_count": 1,
            "unresolved_required_failures": [],
        }
    )

    assert result["retry_decision"] == "response"


def test_retry_route_raises_for_required_failures_after_limit() -> None:
    """required 실패가 남으면 재시도 한도 초과 뒤 요청 실패를 발생시켜야 한다."""

    with pytest.raises(BaseAppException) as error_info:
        retry_route_node.run(
            {
                "batch_tool_failures": [
                    {
                        "tool_call_id": "tool-call-1",
                        "tool_name": "required_tool",
                        "required": True,
                    }
                ],
                "retry_count": 1,
                "unresolved_required_failures": [
                    {
                        "tool_call_id": "tool-call-1",
                        "tool_name": "required_tool",
                        "required": True,
                    }
                ],
            }
        )

    assert error_info.value.detail.code == "TOOL_REQUIRED_FAILURE"
