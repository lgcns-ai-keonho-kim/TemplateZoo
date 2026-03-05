"""
목적: Planner 입력용 히스토리 요약 유틸을 제공한다.
설명: 최근 대화 이력을 role/content 기반 단문 목록으로 변환한다.
디자인 패턴: 유틸리티
참조: src/plan_and_then_execute_agent/core/chat/models/entities.py
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from plan_and_then_execute_agent.core.chat.models import ChatMessage


def summarize_history(history: Sequence[Any], *, limit: int = 6) -> str:
    """Planner 입력용 히스토리 요약 문자열을 생성한다."""

    items = list(history)[-max(1, int(limit)) :]
    lines: list[str] = []
    for item in items:
        role = "system"
        content = ""
        if isinstance(item, ChatMessage):
            role = item.role.value
            content = item.content
        elif isinstance(item, Mapping):
            role = str(item.get("role") or "system").strip().lower()
            content = str(item.get("content") or "")
        else:
            role = str(getattr(item, "role", "system") or "system").strip().lower()
            content = str(getattr(item, "content", "") or "")
        normalized = content.strip().replace("\n", " ")
        if len(normalized) > 280:
            normalized = f"{normalized[:280]}..."
        lines.append(f"[{role}] {normalized}")

    if not lines:
        return "(empty)"
    return "\n".join(lines)

