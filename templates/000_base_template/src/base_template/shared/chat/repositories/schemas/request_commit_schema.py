"""
목적: Chat 요청 커밋 컬렉션 스키마를 제공한다.
설명: request_id 기반 저장 멱등성 기록용 CollectionSchema 생성 책임을 분리한다.
디자인 패턴: 팩토리 함수 패턴
참조: src/base_template/shared/chat/repositories/history_repository.py
"""

from __future__ import annotations

from base_template.core.chat.const import CHAT_REQUEST_COMMIT_COLLECTION
from base_template.integrations.db.base import CollectionSchema, ColumnSpec


def build_chat_request_commit_schema() -> CollectionSchema:
    """요청 커밋 컬렉션 스키마를 생성한다."""

    return CollectionSchema(
        name=CHAT_REQUEST_COMMIT_COLLECTION,
        primary_key="request_id",
        payload_field=None,
        columns=[
            ColumnSpec(name="request_id", data_type="TEXT", is_primary=True),
            ColumnSpec(name="session_id", data_type="TEXT"),
            ColumnSpec(name="message_id", data_type="TEXT"),
            ColumnSpec(name="created_at", data_type="TEXT"),
        ],
    )

