"""
목적: Tool 실행 결과 수집 노드의 실패 분류를 검증한다.
설명: 미해결 실패 병합 시 required/optional 실패가 분리되고 성공 결과가 기존 실패를 해소하는지 확인한다.
디자인 패턴: 단위 테스트
참조: src/tool_proxy_agent/core/chat/nodes/tool_execute_collect_node.py
"""

from __future__ import annotations

from tool_proxy_agent.core.chat.nodes.tool_execute_collect_node import (
    tool_execute_collect_node,
)


def test_tool_execute_collect_splits_required_and_optional_failures() -> None:
    """수집 노드는 required/optional 실패 목록을 별도로 계산해야 한다."""

    result = tool_execute_collect_node.run(
        {
            "completed_tool_results": [],
            "unresolved_tool_failures": [
                {
                    "tool_call_id": "required-1",
                    "tool_name": "required_tool",
                    "required": True,
                    "error": "first failure",
                },
                {
                    "tool_call_id": "optional-1",
                    "tool_name": "optional_tool",
                    "required": False,
                    "error": "old optional failure",
                },
            ],
            "batch_tool_results": [
                {
                    "tool_call_id": "retry-optional-1",
                    "retry_for": "optional-1",
                    "tool_name": "optional_tool",
                    "required": False,
                    "output": {"value": "resolved"},
                }
            ],
            "batch_tool_failures": [
                {
                    "tool_call_id": "optional-2",
                    "tool_name": "optional_tool_b",
                    "required": False,
                    "error": "new optional failure",
                }
            ],
        }
    )

    assert [item["tool_call_id"] for item in result["unresolved_required_failures"]] == [
        "required-1"
    ]
    assert [item["tool_call_id"] for item in result["unresolved_optional_failures"]] == [
        "optional-2"
    ]
    assert [item["tool_call_id"] for item in result["unresolved_tool_failures"]] == [
        "required-1",
        "optional-2",
    ]


def test_tool_execute_collect_keeps_completed_results() -> None:
    """수집 노드는 새 성공 결과를 completed 목록에 반영해야 한다."""

    result = tool_execute_collect_node.run(
        {
            "completed_tool_results": [],
            "unresolved_tool_failures": [],
            "batch_tool_results": [
                {
                    "tool_call_id": "tool-call-1",
                    "tool_name": "sum_tool",
                    "required": True,
                    "output": {"value": 3},
                }
            ],
            "batch_tool_failures": [],
        }
    )

    assert [item["tool_call_id"] for item in result["completed_tool_results"]] == [
        "tool-call-1"
    ]
    assert result["unresolved_required_failures"] == []
    assert result["unresolved_optional_failures"] == []
