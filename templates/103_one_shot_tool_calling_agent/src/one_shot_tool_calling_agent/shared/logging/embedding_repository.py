"""
목적: 임베딩 로그 전용 DB 저장소를 제공한다.
설명: LogRecord를 임베딩 호출 메타 중심 스키마로 분해해 DBClient에 저장한다.
디자인 패턴: 저장소 패턴
참조: src/one_shot_tool_calling_agent/integrations/embedding/client.py, src/one_shot_tool_calling_agent/shared/logging/models.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING, List
from uuid import uuid4

from pydantic import BaseModel

from one_shot_tool_calling_agent.shared.logging.logger import LogRepository
from one_shot_tool_calling_agent.shared.logging.models import LogContext, LogRecord

if TYPE_CHECKING:
    from one_shot_tool_calling_agent.integrations.db import DBClient
    from one_shot_tool_calling_agent.integrations.db.base import (
        CollectionSchema,
        Document,
    )


class EmbeddingLogRepository(LogRepository):
    """임베딩 로그 전용 DB 저장소 구현체."""

    def __init__(
        self,
        client: "DBClient",
        collection: str = "embedding_logs",
        schema: "CollectionSchema | None" = None,
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
        """로그 레코드를 저장한다."""

        from one_shot_tool_calling_agent.integrations.db.base import Document

        self._ensure_ready()
        fields = self._to_fields(record)
        document = Document(doc_id=str(uuid4()), fields=fields)
        self._client.upsert(self._collection, [document])

    def list(self) -> List[LogRecord]:
        """저장된 임베딩 로그 목록을 반환한다."""

        from one_shot_tool_calling_agent.integrations.db.base import Query

        self._ensure_ready()
        documents = self._client.fetch(self._collection, Query())
        records: List[LogRecord] = []
        for document in documents:
            try:
                records.append(self._from_document(document))
            except Exception:  # noqa: BLE001 - 손상 레코드 무시
                continue
        return records

    def _ensure_ready(self) -> None:
        if self._initialized:
            return
        if self._auto_connect:
            self._client.connect()
        if self._auto_create:
            schema = self._schema or self._default_schema(self._collection)
            self._client.create_collection(schema)
        self._initialized = True

    def _default_schema(self, name: str) -> "CollectionSchema":
        from one_shot_tool_calling_agent.integrations.db.base import (
            CollectionSchema,
            ColumnSpec,
        )

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
                ColumnSpec(name="action", data_type="TEXT"),
                ColumnSpec(name="duration_ms", data_type="INTEGER"),
                ColumnSpec(name="success", data_type="INTEGER"),
                ColumnSpec(name="error_type", data_type="TEXT"),
                ColumnSpec(name="input_count", data_type="INTEGER"),
                ColumnSpec(name="input_chars", data_type="INTEGER"),
                ColumnSpec(name="output_count", data_type="INTEGER"),
                ColumnSpec(name="dimension", data_type="INTEGER"),
                ColumnSpec(name="metadata", data_type="TEXT"),
            ],
        )

    def _ensure_db_available(self) -> None:
        from one_shot_tool_calling_agent.integrations.db import DBClient  # noqa: F401

    def _to_fields(self, record: LogRecord) -> dict[str, Any]:
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

        return {
            "timestamp": self._serialize_timestamp(payload.get("timestamp")),
            "level": payload.get("level"),
            "message": payload.get("message"),
            "logger_name": payload.get("logger_name"),
            "trace_id": context.get("trace_id"),
            "span_id": context.get("span_id"),
            "request_id": context.get("request_id"),
            "user_id": context.get("user_id"),
            "tags": self._dump_json(context.get("tags", {})),
            "model_name": metadata.get("model_name"),
            "provider": metadata.get("provider"),
            "action": metadata.get("action"),
            "duration_ms": self._to_int(metadata.get("duration_ms")),
            "success": self._to_bool_int(metadata.get("success")),
            "error_type": metadata.get("error_type"),
            "input_count": self._to_int(metadata.get("input_count")),
            "input_chars": self._to_int(metadata.get("input_chars")),
            "output_count": self._to_int(metadata.get("output_count")),
            "dimension": self._to_int(metadata.get("dimension")),
            "metadata": self._dump_json(metadata),
        }

    def _from_document(self, document: "Document") -> LogRecord:
        fields = document.fields or {}
        metadata = self._load_json(fields.get("metadata"))
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

    def _to_payload(self, record: LogRecord) -> dict[str, Any]:
        if isinstance(record, BaseModel):
            return record.model_dump(mode="json")
        return {
            "level": str(record.level),
            "message": record.message,
            "timestamp": record.timestamp,
            "logger_name": record.logger_name,
            "context": record.context,
            "metadata": record.metadata,
        }

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

    def _load_json(self, raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if raw is None:
            return {}
        if isinstance(raw, str) and raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _to_int(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_bool_int(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return 1 if value else 0
        try:
            return 1 if int(value) else 0
        except (TypeError, ValueError):
            return None


__all__ = ["EmbeddingLogRepository"]
