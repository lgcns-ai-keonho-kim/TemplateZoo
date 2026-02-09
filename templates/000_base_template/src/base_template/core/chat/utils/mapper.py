"""
목적: Chat 이력 문서 매퍼를 제공한다.
설명: 도메인 모델과 Document 간 변환 및 타입 파싱을 담당한다.
디자인 패턴: 매퍼 패턴
참조: src/base_template/core/repositories/chat/history_repository.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from base_template.core.chat.models import ChatMessage, ChatRole, ChatSession, utc_now
from base_template.integrations.db.base import Document


class ChatHistoryMapper:
    """Chat 이력 도메인/문서 매퍼."""

    def session_to_document(self, session: ChatSession) -> Document:
        """세션 모델을 Document로 변환한다."""

        return Document(
            doc_id=session.session_id,
            fields={
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count,
                "last_message_preview": session.last_message_preview,
            },
        )

    def message_to_document(self, message: ChatMessage) -> Document:
        """메시지 모델을 Document로 변환한다."""

        return Document(
            doc_id=message.message_id,
            fields={
                "session_id": message.session_id,
                "role": message.role.value,
                "content": message.content,
                "sequence": message.sequence,
                "created_at": message.created_at.isoformat(),
                "metadata": json.dumps(message.metadata, ensure_ascii=True),
            },
        )

    def session_from_document(self, document: Document) -> ChatSession:
        """Document를 세션 모델로 변환한다."""

        fields = document.fields or {}
        return ChatSession(
            session_id=str(document.doc_id),
            title=str(fields.get("title") or "새 대화"),
            created_at=self._parse_datetime(fields.get("created_at")),
            updated_at=self._parse_datetime(fields.get("updated_at")),
            message_count=self._to_int(fields.get("message_count")),
            last_message_preview=fields.get("last_message_preview"),
        )

    def message_from_document(self, document: Document) -> ChatMessage:
        """Document를 메시지 모델로 변환한다."""

        fields = document.fields or {}
        role_value = str(fields.get("role") or ChatRole.USER.value)
        metadata = self._parse_metadata(fields.get("metadata"))
        role = self._parse_role(role_value)
        return ChatMessage(
            message_id=str(document.doc_id),
            session_id=str(fields.get("session_id") or ""),
            role=role,
            content=str(fields.get("content") or ""),
            sequence=max(self._to_int(fields.get("sequence")), 1),
            created_at=self._parse_datetime(fields.get("created_at")),
            metadata=metadata,
        )

    def preview(self, text: str) -> str:
        """본문에서 미리보기 문자열을 생성한다."""

        compact = " ".join(text.split())
        return compact[:120]

    def _parse_role(self, value: str) -> ChatRole:
        try:
            return ChatRole(value)
        except ValueError:
            return ChatRole.USER

    def _parse_datetime(self, value: object) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                return utc_now()
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        return utc_now()

    def _parse_metadata(self, raw: object) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str) and raw:
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            if isinstance(loaded, dict):
                return loaded
        return {}

    def _to_int(self, value: object) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0
