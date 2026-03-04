"""
목적: LanceDB 문서 매퍼 모듈을 제공한다.
설명: Document 모델과 LanceDB 행 데이터 간 변환을 담당한다.
디자인 패턴: 매퍼 패턴
참조: src/chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from chatbot.integrations.db.base.models import CollectionSchema, Document, Vector
from chatbot.integrations.db.engines.sql_common import vector_field


class LanceDocumentMapper:
    """LanceDB 문서 매퍼."""

    def document_to_row(
        self,
        document: Document,
        schema: CollectionSchema,
    ) -> Dict[str, Any]:
        """문서를 테이블 행 딕셔너리로 변환한다."""

        row: Dict[str, Any] = {schema.primary_key: document.doc_id}
        if schema.payload_field:
            row[schema.payload_field] = json.dumps(document.payload, ensure_ascii=False)

        vector_columns = {column.name for column in schema.columns if column.is_vector}
        target_vector_field = vector_field(schema)
        if target_vector_field:
            vector_columns.add(target_vector_field)

        for key, value in document.fields.items():
            if key in vector_columns:
                parsed_values = self._coerce_vector_values(value)
                if parsed_values is not None:
                    row[key] = parsed_values
                    continue
            row[key] = value

        if target_vector_field and document.vector is not None:
            row[target_vector_field] = [float(item) for item in document.vector.values]

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
        include_vector: bool = True,
    ) -> Document:
        """행 딕셔너리를 문서 모델로 변환한다."""

        doc_id = row.get(schema.primary_key)
        payload: Dict[str, Any] = {}
        if schema.payload_field:
            raw_payload = row.get(schema.payload_field)
            if isinstance(raw_payload, str):
                payload = json.loads(raw_payload) if raw_payload else {}
            elif isinstance(raw_payload, dict):
                payload = raw_payload
            elif raw_payload is None:
                payload = {}
            else:
                payload = {"value": raw_payload}

        target_vector_field = vector_field(schema)
        vector: Optional[Vector] = None
        if include_vector and target_vector_field:
            parsed_vector = self._coerce_vector_values(row.get(target_vector_field))
            if parsed_vector is not None:
                vector = Vector(values=parsed_vector, dimension=len(parsed_vector))

        additional_vector_fields = {
            column.name
            for column in schema.columns
            if column.is_vector and column.name != target_vector_field
        }
        fields: Dict[str, Any] = {}
        for key, value in row.items():
            if key in {schema.primary_key, schema.payload_field, target_vector_field}:
                continue
            if key in additional_vector_fields:
                parsed_values = self._coerce_vector_values(value)
                if parsed_values is not None:
                    fields[key] = parsed_values
                    continue
            fields[key] = value
        return Document(doc_id=doc_id, fields=fields, payload=payload, vector=vector)

    def _coerce_vector_values(self, value: Any) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, Vector):
            return [float(item) for item in value.values]
        if isinstance(value, list):
            if not value:
                return None
            normalized: list[float] = []
            for item in value:
                if not isinstance(item, (int, float, str)):
                    return None
                try:
                    normalized.append(float(item))
                except (TypeError, ValueError):
                    return None
            return normalized
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError:
                return None
            if not isinstance(decoded, list) or not decoded:
                return None
            normalized: list[float] = []
            for item in decoded:
                if not isinstance(item, (int, float, str)):
                    return None
                try:
                    normalized.append(float(item))
                except (TypeError, ValueError):
                    return None
            return normalized
        return None
