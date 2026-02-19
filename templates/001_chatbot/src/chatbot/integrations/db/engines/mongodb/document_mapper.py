"""
목적: MongoDB 문서 매퍼 모듈을 제공한다.
설명: Document 모델과 MongoDB 레코드 간 변환을 담당한다.
디자인 패턴: 매퍼 패턴
참조: src/chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

from typing import Dict

from chatbot.integrations.db.base.models import CollectionSchema, Document, Vector


class MongoDocumentMapper:
    """MongoDB 문서 매퍼."""

    def to_update_payload(self, document: Document, schema: CollectionSchema) -> Dict[str, object]:
        """업서트용 `$set` 페이로드를 생성한다."""

        payload: Dict[str, object] = {}
        if schema.payload_field:
            payload[schema.payload_field] = dict(document.payload)
        else:
            payload.update(document.fields)
        if schema.vector_field and document.vector:
            payload[schema.vector_field] = document.vector.values
        return payload

    def from_record(self, data: Dict[str, object], schema: CollectionSchema) -> Document:
        """MongoDB 레코드를 Document 모델로 변환한다."""

        payload = data.get(schema.payload_field, {}) if schema.payload_field else {}
        vector = None
        if schema.vector_field:
            raw_vector = data.get(schema.vector_field)
            if raw_vector is not None:
                vector = Vector(values=list(raw_vector), dimension=len(raw_vector))
        fields = {}
        if not schema.payload_field:
            fields = {
                key: value
                for key, value in data.items()
                if key not in {"_id", schema.vector_field}
            }
        return Document(
            doc_id=str(data["_id"]),
            fields=fields,
            payload=payload,
            vector=vector,
        )
