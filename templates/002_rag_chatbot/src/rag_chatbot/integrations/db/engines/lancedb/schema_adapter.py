"""
목적: LanceDB 스키마/행 변환 어댑터를 제공한다.
설명: CollectionSchema를 PyArrow 스키마로 변환하고, 입력 row를 스키마 타입으로 정규화한다.
디자인 패턴: 어댑터 패턴
참조: src/rag_chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

import json
from typing import Any, Optional

from rag_chatbot.integrations.db.base.models import CollectionSchema, ColumnSpec
from rag_chatbot.integrations.db.engines.sql_common import vector_field

pa: Any | None
try:
    import pyarrow as _pa
except ImportError:  # pragma: no cover - 환경 의존 로딩
    pa = None
else:  # pragma: no cover - 환경 의존 로딩
    pa = _pa


class LanceSchemaAdapter:
    """LanceDB 스키마/행 변환 어댑터."""

    def build_arrow_schema(self, schema: CollectionSchema):
        if pa is None:
            raise RuntimeError("pyarrow 패키지가 설치되어 있지 않습니다.")

        fields: list[Any] = []
        names: set[str] = set()
        for column in schema.columns:
            fields.append(self.build_arrow_field(column, schema))
            names.add(column.name)

        if schema.primary_key not in names:
            fields.insert(0, pa.field(schema.primary_key, pa.string(), nullable=False))
            names.add(schema.primary_key)

        if schema.payload_field and schema.payload_field not in names:
            fields.append(pa.field(schema.payload_field, pa.string(), nullable=True))
            names.add(schema.payload_field)

        target_vector_field = vector_field(schema)
        if target_vector_field and target_vector_field not in names:
            vector_dimension = schema.resolve_vector_dimension()
            if vector_dimension is None:
                raise ValueError("벡터 차원 정보가 필요합니다.")
            fields.append(
                pa.field(
                    target_vector_field,
                    pa.list_(pa.float32(), int(vector_dimension)),
                    nullable=True,
                )
            )

        return pa.schema(fields)

    def build_arrow_field(self, column: ColumnSpec, schema: CollectionSchema):
        if pa is None:
            raise RuntimeError("pyarrow 패키지가 설치되어 있지 않습니다.")

        target_vector_field = vector_field(schema)
        if column.is_vector or (target_vector_field and column.name == target_vector_field):
            vector_dimension = column.dimension or schema.resolve_vector_dimension()
            if vector_dimension is None:
                raise ValueError("벡터 차원 정보가 필요합니다.")
            return pa.field(
                column.name,
                pa.list_(pa.float32(), int(vector_dimension)),
                nullable=column.nullable,
            )

        return pa.field(
            column.name,
            self._resolve_arrow_type(column.data_type),
            nullable=column.nullable,
        )

    def normalize_row(
        self,
        row: dict[str, Any],
        arrow_schema,
        schema: CollectionSchema,
    ) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        target_vector_field = vector_field(schema)
        vector_columns = {
            column.name
            for column in schema.columns
            if column.is_vector
        }
        if target_vector_field:
            vector_columns.add(target_vector_field)

        for field in arrow_schema:
            value = row.get(field.name)
            if field.name in vector_columns:
                normalized[field.name] = self._coerce_vector(value, field)
                continue
            normalized[field.name] = self._coerce_scalar(value, field)

        if schema.primary_key not in normalized:
            normalized[schema.primary_key] = row.get(schema.primary_key)

        return normalized

    def _resolve_arrow_type(self, data_type: Optional[str]):
        if pa is None:
            raise RuntimeError("pyarrow 패키지가 설치되어 있지 않습니다.")

        if not data_type:
            return pa.string()
        normalized = data_type.strip().lower()
        if normalized in {"text", "string", "varchar", "char", "keyword"}:
            return pa.string()
        if normalized in {"integer", "int", "bigint", "smallint"}:
            return pa.int64()
        if normalized in {"real", "float", "double", "numeric"}:
            return pa.float64()
        if normalized in {"bool", "boolean"}:
            return pa.bool_()
        if normalized in {"binary", "blob"}:
            return pa.binary()
        return pa.string()

    def _coerce_vector(self, value: Any, field) -> Any:
        if value is None:
            return None
        if pa is None:
            raise RuntimeError("pyarrow 패키지가 설치되어 있지 않습니다.")

        values: list[float]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            decoded = json.loads(text)
            if not isinstance(decoded, list):
                raise ValueError("벡터 문자열은 JSON 배열이어야 합니다.")
            values = [float(item) for item in decoded]
        elif isinstance(value, list):
            values = [float(item) for item in value]
        else:
            raise ValueError("벡터 값은 리스트 또는 JSON 문자열이어야 합니다.")

        if pa.types.is_fixed_size_list(field.type):
            expected = int(field.type.list_size)
            if expected != len(values):
                raise ValueError(
                    f"벡터 차원이 일치하지 않습니다. expected={expected}, actual={len(values)}"
                )
        return values

    def _coerce_scalar(self, value: Any, field) -> Any:
        if value is None:
            return None
        if pa is None:
            raise RuntimeError("pyarrow 패키지가 설치되어 있지 않습니다.")

        if pa.types.is_string(field.type):
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            return str(value)
        if pa.types.is_integer(field.type):
            return int(value)
        if pa.types.is_floating(field.type):
            return float(value)
        if pa.types.is_boolean(field.type):
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"1", "true", "yes", "on"}:
                    return True
                if lowered in {"0", "false", "no", "off"}:
                    return False
            return bool(value)
        if pa.types.is_binary(field.type):
            if isinstance(value, bytes):
                return value
            return str(value).encode("utf-8")
        return value
