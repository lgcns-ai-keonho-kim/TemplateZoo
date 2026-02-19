"""
목적: Redis 키스페이스 유틸 모듈을 제공한다.
설명: 키 생성 규칙과 SCAN 기반 키 수집을 담당한다.
디자인 패턴: 유틸리티 클래스
참조: src/chatbot/integrations/db/engines/redis/engine.py
"""

from __future__ import annotations

from typing import List

from chatbot.integrations.db.base.models import CollectionSchema


class RedisKeyspaceHelper:
    """Redis 키스페이스 도우미."""

    def payload_storage_key(self, schema: CollectionSchema) -> str:
        """payload 저장 필드명을 반환한다."""

        return schema.payload_field or "fields"

    def make_key(self, collection: str, doc_id: object) -> str:
        """문서 저장 키를 생성한다."""

        return f"{collection}:{doc_id}"

    def scan_keys(self, client, pattern: str) -> List[bytes]:
        """패턴에 해당하는 키를 모두 조회한다."""

        cursor = 0
        keys: List[bytes] = []
        while True:
            cursor, batch = client.scan(cursor=cursor, match=pattern, count=200)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys
