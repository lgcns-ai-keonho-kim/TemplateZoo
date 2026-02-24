"""
목적: Redis 문서 매퍼 모듈을 제공한다.
설명: Document 모델과 Redis Hash 데이터 간 변환을 담당한다.
디자인 패턴: 매퍼 패턴
참조: src/rag_chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

import json
from typing import Dict, Optional

from rag_chatbot.integrations.db.base.models import CollectionSchema, Document, Vector
from rag_chatbot.integrations.db.engines.redis.keyspace import RedisKeyspaceHelper


class RedisDocumentMapper:
    """Redis 문서 매퍼."""

    def __init__(self, keyspace: RedisKeyspaceHelper) -> None:
        self._keyspace = keyspace

    def to_hash_mapping(self, document: Document, schema: CollectionSchema) -> Dict[str, str]:
        """문서를 Redis Hash 매핑으로 변환한다."""

        payload_key = self._keyspace.payload_storage_key(schema)
        mapping: Dict[str, str] = {}
        if schema.payload_field:
            mapping[payload_key] = json.dumps(document.payload)
        else:
            mapping[payload_key] = json.dumps(document.fields)
        if schema.vector_field and document.vector:
            mapping[schema.vector_field] = json.dumps(document.vector.values)
        return mapping

    def from_hash(
        self,
        doc_id: object,
        data: Dict[bytes, bytes],
        schema: CollectionSchema,
    ) -> Document:
        """Redis Hash 데이터를 문서 모델로 변환한다."""

        payload_key = self._keyspace.payload_storage_key(schema)
        raw_payload = data.get(payload_key.encode(), b"{}").decode()
        payload_data = json.loads(raw_payload) if raw_payload else {}
        vector = self._parse_vector(data, schema)
        if schema.payload_field:
            return Document(doc_id=doc_id, fields={}, payload=payload_data, vector=vector)
        return Document(doc_id=doc_id, fields=payload_data, payload={}, vector=vector)

    def _parse_vector(
        self,
        data: Dict[bytes, bytes],
        schema: CollectionSchema,
    ) -> Optional[Vector]:
        if not schema.vector_field:
            return None
        raw_vector = data.get(schema.vector_field.encode())
        if not raw_vector:
            return None
        values = json.loads(raw_vector.decode())
        return Vector(values=values, dimension=len(values))
