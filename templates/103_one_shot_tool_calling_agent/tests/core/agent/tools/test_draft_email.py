"""
목적: draft_email Tool 동작을 검증한다.
설명: 필수 인자 검증과 mock 초안 생성 결과를 실제 Tool 함수 기준으로 확인한다.
디자인 패턴: 단위 테스트
참조: src/one_shot_tool_calling_agent/core/agent/tools/draft_email.py
"""

from __future__ import annotations

from one_shot_tool_calling_agent.core.agent.tools.draft_email import draft_email


def test_draft_email_returns_mock_body() -> None:
    """필수 인자가 주어지면 mock 이메일 초안을 반환해야 한다."""

    result = draft_email(
        {
            "tool_call_id": "tool-1",
            "tool_name": "draft_email",
            "args": {
                "recipient": "김대리",
                "subject": "일정 조율",
                "purpose": "다음 주 회의 가능한 시간을 문의합니다.",
                "tone": "정중한",
            },
            "session_id": "run-1",
            "request_id": "run-1",
            "retry_for": None,
            "state": {},
        }
    )

    assert result["ok"] is True
    assert result["output"]["recipient"] == "김대리"
    assert result["output"]["mock"] is True
    assert "다음 주 회의 가능한 시간을 문의합니다." in result["output"]["body"]


def test_draft_email_rejects_missing_required_fields() -> None:
    """필수 인자가 비어 있으면 실패 결과를 반환해야 한다."""

    result = draft_email(
        {
            "tool_call_id": "tool-2",
            "tool_name": "draft_email",
            "args": {
                "recipient": "",
                "subject": "일정 조율",
                "purpose": "",
            },
            "session_id": "run-2",
            "request_id": "run-2",
            "retry_for": None,
            "state": {},
        }
    )

    assert result["ok"] is False
    assert "recipient, subject, purpose" in str(result["error"])
