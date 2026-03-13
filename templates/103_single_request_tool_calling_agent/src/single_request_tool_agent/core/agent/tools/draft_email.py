"""
목적: 이메일 초안 작성 Tool 예시를 제공한다.
설명: 실제 메일 발송 없이 입력된 목적을 바탕으로 mock 이메일 초안을 생성한다.
디자인 패턴: 단일 책임 함수
참조: src/single_request_tool_agent/shared/agent/tools/types.py
"""

from __future__ import annotations

from typing import Any

from single_request_tool_agent.shared.agent.tools.types import ToolCall, ToolResult


def draft_email(tool_call: ToolCall) -> ToolResult:
    """이메일 초안 mock 결과를 반환한다."""

    args: dict[str, Any] = dict(tool_call.get("args") or {})
    recipient = str(args.get("recipient") or "").strip()
    subject = str(args.get("subject") or "").strip()
    purpose = str(args.get("purpose") or "").strip()
    tone = str(args.get("tone") or "정중한").strip() or "정중한"

    if not recipient or not subject or not purpose:
        return {
            "ok": False,
            "output": {},
            "error": "recipient, subject, purpose 인자는 모두 필요합니다.",
        }

    body = (
        f"{recipient}님,\n\n"
        f"{purpose}\n\n"
        f"위 내용을 {tone} 톤으로 전달드립니다.\n\n"
        "감사합니다."
    )
    return {
        "ok": True,
        "output": {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "tone": tone,
            "mock": True,
        },
        "error": None,
    }
