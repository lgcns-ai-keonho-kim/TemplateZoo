"""
목적: LLM 로그 전용 DB 저장소를 제공한다.
설명: LogRecord를 LLM 컬럼 스키마로 분해해 DBClient에 저장한다.
디자인 패턴: 저장소 패턴
참조: src/base_template/shared/logging/models.py, src/base_template/integrations/llm/client.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel

from base_template.shared.logging.logger import LogRepository
from base_template.shared.logging.models import LogContext, LogRecord

if TYPE_CHECKING:
    from base_template.integrations.db import DBClient
    from base_template.integrations.db.base import CollectionSchema, ColumnSpec, Document, Query


class LLMLogRepository(LogRepository):
    """LLM 로그 전용 DB 저장소 구현체."""

    def __init__(
        self,
        client: "DBClient",
        collection: str = "llm_logs",
        schema: Optional["CollectionSchema"] = None,
        auto_create: bool = True,
        auto_connect: bool = False,
    ) -> None:
        self._ensure_db_available()
        self._client = client
        self._collection = collection
        self._schema = schema
        self._auto_create = auto_create
        self._auto_connect = auto_connect
        self._initialized = False

    def add(self, record: LogRecord) -> None:
        from base_template.integrations.db.base import Document

        self._ensure_ready()
        fields = self._to_fields(record)
        document = Document(doc_id=str(uuid4()), fields=fields)
        self._client.upsert(self._collection, [document])

    def list(self) -> List[LogRecord]:
        from base_template.integrations.db.base import Query

        self._ensure_ready()
        documents = self._client.fetch(self._collection, Query())
        records: List[LogRecord] = []
        for document in documents:
            try:
                record = self._from_document(document)
            except Exception:  # noqa: BLE001 - 손상된 레코드 스킵
                continue
            records.append(record)
        return records

    def _ensure_ready(self) -> None:
        from base_template.integrations.db.base import CollectionSchema

        if self._initialized:
            return
        if self._auto_connect:
            self._client.connect()
        if self._auto_create:
            schema = self._schema or self._default_schema(self._collection)
            self._client.create_collection(schema)
        self._initialized = True

    def _default_schema(self, name: str) -> "CollectionSchema":
        from base_template.integrations.db.base import CollectionSchema, ColumnSpec

        return CollectionSchema(
            name=name,
            primary_key="log_id",
            payload_field=None,
            columns=[
                ColumnSpec(name="log_id", data_type="TEXT", is_primary=True),
                ColumnSpec(name="timestamp", data_type="TEXT"),
                ColumnSpec(name="level", data_type="TEXT"),
                ColumnSpec(name="message", data_type="TEXT"),
                ColumnSpec(name="logger_name", data_type="TEXT"),
                ColumnSpec(name="trace_id", data_type="TEXT"),
                ColumnSpec(name="span_id", data_type="TEXT"),
                ColumnSpec(name="request_id", data_type="TEXT"),
                ColumnSpec(name="user_id", data_type="TEXT"),
                ColumnSpec(name="tags", data_type="TEXT"),
                ColumnSpec(name="model_name", data_type="TEXT"),
                ColumnSpec(name="provider", data_type="TEXT"),
                ColumnSpec(name="llm_type", data_type="TEXT"),
                ColumnSpec(name="action", data_type="TEXT"),
                ColumnSpec(name="duration_ms", data_type="INTEGER"),
                ColumnSpec(name="success", data_type="INTEGER"),
                ColumnSpec(name="error_type", data_type="TEXT"),
                ColumnSpec(name="input_tokens", data_type="INTEGER"),
                ColumnSpec(name="output_tokens", data_type="INTEGER"),
                ColumnSpec(name="total_tokens", data_type="INTEGER"),
                ColumnSpec(name="input_cost", data_type="REAL"),
                ColumnSpec(name="output_cost", data_type="REAL"),
                ColumnSpec(name="total_cost", data_type="REAL"),
                ColumnSpec(name="input_token_details", data_type="TEXT"),
                ColumnSpec(name="output_token_details", data_type="TEXT"),
                ColumnSpec(name="input_cost_details", data_type="TEXT"),
                ColumnSpec(name="output_cost_details", data_type="TEXT"),
                ColumnSpec(name="metadata", data_type="TEXT"),
            ],
        )

    def _ensure_db_available(self) -> None:
        try:
            from base_template.integrations.db import DBClient  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("DB 통합 모듈을 불러올 수 없습니다.") from exc

    def _to_fields(self, record: LogRecord) -> Dict[str, Any]:
        payload = self._to_payload(record)
        context = payload.get("context") or {}
        if isinstance(context, BaseModel):
            context = context.model_dump(mode="json")
        if not isinstance(context, dict):
            context = {}
        metadata = payload.get("metadata") or {}
        if isinstance(metadata, BaseModel):
            metadata = metadata.model_dump(mode="json")
        if not isinstance(metadata, dict):
            metadata = {}
        usage = metadata.get("usage_metadata") or {}
        if not isinstance(usage, dict):
            usage = {}
        model_name = metadata.get("model_name") or metadata.get("ls_model_name")
        provider = metadata.get("provider") or metadata.get("ls_provider")
        fields = {
            "timestamp": self._serialize_timestamp(payload.get("timestamp")),
            "level": payload.get("level"),
            "message": payload.get("message"),
            "logger_name": payload.get("logger_name"),
            "trace_id": context.get("trace_id"),
            "span_id": context.get("span_id"),
            "request_id": context.get("request_id"),
            "user_id": context.get("user_id"),
            "tags": self._dump_json(context.get("tags", {})),
            "model_name": model_name,
            "provider": provider,
            "llm_type": metadata.get("llm_type"),
            "action": metadata.get("action"),
            "duration_ms": self._to_int(metadata.get("duration_ms")),
            "success": self._to_bool_int(metadata.get("success")),
            "error_type": metadata.get("error_type"),
            "input_tokens": self._to_int(usage.get("input_tokens")),
            "output_tokens": self._to_int(usage.get("output_tokens")),
            "total_tokens": self._to_int(usage.get("total_tokens")),
            "input_cost": self._to_float(usage.get("input_cost")),
            "output_cost": self._to_float(usage.get("output_cost")),
            "total_cost": self._to_float(usage.get("total_cost")),
            "input_token_details": self._dump_json(usage.get("input_token_details")),
            "output_token_details": self._dump_json(usage.get("output_token_details")),
            "input_cost_details": self._dump_json(usage.get("input_cost_details")),
            "output_cost_details": self._dump_json(usage.get("output_cost_details")),
            "metadata": self._dump_json(metadata),
        }
        return fields

    def _from_document(self, document: "Document") -> LogRecord:
        fields = document.fields or {}
        metadata = self._load_json(fields.get("metadata"))
        usage_metadata = {
            "input_tokens": self._to_int(fields.get("input_tokens")),
            "output_tokens": self._to_int(fields.get("output_tokens")),
            "total_tokens": self._to_int(fields.get("total_tokens")),
            "input_cost": self._to_float(fields.get("input_cost")),
            "output_cost": self._to_float(fields.get("output_cost")),
            "total_cost": self._to_float(fields.get("total_cost")),
            "input_token_details": self._load_json(fields.get("input_token_details")),
            "output_token_details": self._load_json(fields.get("output_token_details")),
            "input_cost_details": self._load_json(fields.get("input_cost_details")),
            "output_cost_details": self._load_json(fields.get("output_cost_details")),
        }
        metadata["usage_metadata"] = usage_metadata
        data = {
            "level": fields.get("level"),
            "message": fields.get("message"),
            "timestamp": self._parse_timestamp(fields.get("timestamp")),
            "logger_name": fields.get("logger_name"),
            "context": LogContext(
                trace_id=fields.get("trace_id"),
                span_id=fields.get("span_id"),
                request_id=fields.get("request_id"),
                user_id=fields.get("user_id"),
                tags=self._load_json(fields.get("tags")),
            ),
            "metadata": metadata,
        }
        return LogRecord.model_validate(data)

    def _to_payload(self, record: LogRecord) -> dict:
        if isinstance(record, BaseModel):
            payload = record.model_dump(mode="json")
        else:
            payload = {
                "level": str(record.level),
                "message": record.message,
                "timestamp": record.timestamp,
                "logger_name": record.logger_name,
                "context": record.context,
                "metadata": record.metadata,
            }
        return payload

    def _serialize_timestamp(self, value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return datetime.now(timezone.utc).isoformat()

    def _parse_timestamp(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                parsed = datetime.now(timezone.utc)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        return datetime.now(timezone.utc)

    def _dump_json(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=True)
        except TypeError:
            return json.dumps(str(value), ensure_ascii=True)

    def _load_json(self, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if raw is None:
            return {}
        if isinstance(raw, str) and raw:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            if isinstance(data, dict):
                return data
        return {}

    def _to_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_bool_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return 1 if value else 0
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"true", "1", "yes"}:
                return 1
            if lowered in {"false", "0", "no"}:
                return 0
        return None
