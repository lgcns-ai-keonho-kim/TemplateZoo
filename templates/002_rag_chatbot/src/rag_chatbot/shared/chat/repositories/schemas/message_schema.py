"""
목적: Chat 메시지 컬렉션 스키마를 제공한다.
설명: 메시지 저장용 CollectionSchema 생성 책임을 분리한다.
디자인 패턴: 팩토리 함수 패턴
참조: src/rag_chatbot/shared/chat/repositories/history_repository.py
"""

from __future__ import annotations

from rag_chatbot.core.chat.const import CHAT_MESSAGE_COLLECTION
from rag_chatbot.integrations.db.base import CollectionSchema, ColumnSpec


def build_chat_message_schema() -> CollectionSchema:
    """메시지 컬렉션 스키마를 생성한다."""

    return CollectionSchema(
        name=CHAT_MESSAGE_COLLECTION,
        primary_key="message_id",
        payload_field=None,
        columns=[
            ColumnSpec(name="message_id", data_type="TEXT", is_primary=True),
            ColumnSpec(name="session_id", data_type="TEXT"),
            ColumnSpec(name="role", data_type="TEXT"),
            ColumnSpec(name="content", data_type="TEXT"),
            ColumnSpec(name="sequence", data_type="INTEGER"),
            ColumnSpec(name="created_at", data_type="TEXT"),
            ColumnSpec(name="metadata", data_type="TEXT"),
        ],
    )
