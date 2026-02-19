"""
목적: Elasticsearch 문서 매퍼 모듈을 제공한다.
설명: Document 모델과 Elasticsearch 히트 데이터 간 변환을 담당한다.
디자인 패턴: 매퍼 패턴
참조: src/chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

from chatbot.integrations.db.base.models import CollectionSchema, Document, Vector


class ElasticDocumentMapper:
    """Elasticsearch 문서 매퍼."""

    def to_index_document(self, document: Document, schema: CollectionSchema) -> dict:
        """인덱싱용 문서 본문을 생성한다."""

        body = {}
        if schema.payload_field:
            body[schema.payload_field] = document.payload
        else:
            body.update(document.fields)
        if schema.vector_field and document.vector:
            body[schema.vector_field] = document.vector.values
        return body

    def from_hit(
        self,
        hit: dict,
        schema: CollectionSchema,
        include_vector: bool = True,
    ) -> Document:
        """검색 히트를 Document 모델로 변환한다."""

        source = hit.get("_source", {})
        payload = source.get(schema.payload_field, {}) if schema.payload_field else {}
        vector = None
        if include_vector and schema.vector_field:
            raw_vector = source.get(schema.vector_field)
            if raw_vector is not None:
                vector = Vector(values=raw_vector, dimension=len(raw_vector))
        return Document(
            doc_id=hit.get("_id"),
            fields={},
            payload=payload,
            vector=vector,
        )
