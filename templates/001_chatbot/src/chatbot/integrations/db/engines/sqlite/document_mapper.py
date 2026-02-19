"""
목적: SQLite 문서 매퍼 모듈을 제공한다.
설명: Document 모델과 SQLite 행 데이터 간 변환을 담당한다.
디자인 패턴: 매퍼 패턴
참조: src/chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

from chatbot.integrations.db.base.models import CollectionSchema, Document, Vector


class SqliteDocumentMapper:
    """SQLite 문서 매퍼."""

    def __init__(
        self,
        vector_loader: Callable[[CollectionSchema, object], Optional[Vector]],
    ) -> None:
        self._vector_loader = vector_loader

    def document_to_row(
        self,
        document: Document,
        schema: CollectionSchema,
    ) -> Dict[str, Any]:
        """문서를 테이블 행 딕셔너리로 변환한다."""

        row: Dict[str, Any] = {schema.primary_key: document.doc_id}
        if schema.payload_field:
            row[schema.payload_field] = json.dumps(document.payload)
        for key, value in document.fields.items():
            row[key] = value
        if schema.columns:
            allowed = set(schema.column_names())
            allowed.add(schema.primary_key)
            if schema.payload_field:
                allowed.add(schema.payload_field)
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
            if isinstance(raw, str):
                payload = json.loads(raw) if raw else {}
            elif isinstance(raw, dict):
                payload = raw
            elif raw is None:
                payload = {}
            else:
                payload = {"value": raw}
        vector = self._vector_loader(schema, doc_id)
        fields = {
            key: value
            for key, value in row.items()
            if key not in {schema.primary_key, schema.payload_field}
        }
        return Document(doc_id=doc_id, fields=fields, payload=payload, vector=vector)
