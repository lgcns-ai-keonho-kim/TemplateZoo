"""
목적: Chat 세션 컬렉션 스키마를 제공한다.
설명: 세션 저장용 CollectionSchema 생성 책임을 분리한다.
디자인 패턴: 팩토리 함수 패턴
참조: src/chatbot/shared/chat/repositories/history_repository.py
"""

from __future__ import annotations

from chatbot.core.chat.const import CHAT_SESSION_COLLECTION
from chatbot.integrations.db.base import CollectionSchema, ColumnSpec


def build_chat_session_schema() -> CollectionSchema:
    """세션 컬렉션 스키마를 생성한다."""

    return CollectionSchema(
        name=CHAT_SESSION_COLLECTION,
        primary_key="session_id",
        payload_field=None,
        columns=[
            ColumnSpec(name="session_id", data_type="TEXT", is_primary=True),
            ColumnSpec(name="title", data_type="TEXT"),
            ColumnSpec(name="created_at", data_type="TEXT"),
            ColumnSpec(name="updated_at", data_type="TEXT"),
            ColumnSpec(name="message_count", data_type="INTEGER"),
            ColumnSpec(name="last_message_preview", data_type="TEXT"),
        ],
    )
