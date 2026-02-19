"""
목적: PostgreSQL 문서 매퍼 모듈을 제공한다.
설명: Document 모델과 PostgreSQL 행 데이터 간 변환을 담당한다.
디자인 패턴: 매퍼 패턴
참조: src/chatbot/integrations/db/engines/postgres/vector_adapter.py
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

from chatbot.integrations.db.base.models import CollectionSchema, Document, Vector
from chatbot.integrations.db.engines.sql_common import vector_field
from chatbot.integrations.db.engines.postgres.vector_adapter import (
    PostgresVectorAdapter,
)


class PostgresDocumentMapper:
    """PostgreSQL 문서 매퍼."""

    def __init__(
        self,
        vector_adapter: PostgresVectorAdapter,
        json_value_encoder: Callable[[Dict[str, Any]], object],
    ) -> None:
        self._vector_adapter = vector_adapter
        self._json_value_encoder = json_value_encoder

    def document_to_row(
        self,
        document: Document,
        schema: CollectionSchema,
    ) -> Dict[str, Any]:
        """문서를 테이블 행 딕셔너리로 변환한다."""

        row: Dict[str, Any] = {schema.primary_key: document.doc_id}
        if schema.payload_field:
            row[schema.payload_field] = self._json_value_encoder(document.payload)
        for key, value in document.fields.items():
            row[key] = value
        target_vector_field = vector_field(schema)
        if target_vector_field and document.vector:
            row[target_vector_field] = self._vector_adapter.param(document.vector.values)
        if schema.columns:
            allowed = set(schema.column_names())
            allowed.add(schema.primary_key)
            if schema.payload_field:
                allowed.add(schema.payload_field)
            if target_vector_field:
                allowed.add(target_vector_field)
            row = {key: value for key, value in row.items() if key in allowed}
        return row

    def row_to_document(
        self,
        row: Dict[str, Any],
        schema: CollectionSchema,
    ) -> Document:
        """행 딕셔너리를 문서 모델로 변환한다."""

        doc_id = row.get(schema.primary_key)
        payload: Dict[str, Any] = {}
        if schema.payload_field:
            raw = row.get(schema.payload_field)
            if isinstance(raw, memoryview):
                raw = raw.tobytes()
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode()
            if isinstance(raw, str):
                payload = json.loads(raw) if raw else {}
            elif isinstance(raw, dict):
                payload = raw
            elif raw is None:
                payload = {}
            else:
                payload = {"value": raw}
        vector: Optional[Vector] = None
        target_vector_field = vector_field(schema)
        if target_vector_field:
            raw_vector = row.get(target_vector_field)
            if raw_vector is not None:
                values = self._vector_adapter.parse(raw_vector)
                if values is not None:
                    vector = Vector(values=values, dimension=len(values))
        fields = {
            key: value
            for key, value in row.items()
            if key not in {schema.primary_key, schema.payload_field, target_vector_field}
        }
        return Document(doc_id=doc_id, fields=fields, payload=payload, vector=vector)
