"""
목적: Redis 기반 DB 엔진을 제공한다.
설명: 스키마 기반 필드 저장과 간단한 검색을 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/integrations/db/base/engine.py
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Optional, Tuple

from ....shared.logging import Logger, create_default_logger
from ..base.engine import BaseDBEngine
from ..base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    Query,
    Vector,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)

try:
    import redis
except ImportError:  # pragma: no cover - 환경 의존 로딩
    redis = None


class RedisEngine(BaseDBEngine):
    """Redis 기반 엔진 구현체."""

    def __init__(
        self,
        url: Optional[str] = None,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        username: Optional[str] = None,
        password: Optional[str] = None,
        scheme: str = "redis",
        logger: Optional[Logger] = None,
        enable_vector: bool = False,
    ) -> None:
        if not url:
            auth = ""
            if username and password:
                auth = f"{username}:{password}@"
            elif password:
                auth = f":{password}@"
            url = f"{scheme}://{auth}{host}:{port}/{db}"
        self._url = url
        self._logger = logger or create_default_logger("RedisEngine")
        self._enable_vector = enable_vector
        self._client = None

    @property
    def name(self) -> str:
        return "redis"

    @property
    def supports_vector_search(self) -> bool:
        return self._enable_vector

    def connect(self) -> None:
        if redis is None:
            raise RuntimeError("redis 패키지가 설치되어 있지 않습니다.")
        if self._client is not None:
            return
        self._client = redis.Redis.from_url(self._url)
        self._logger.info("Redis 연결이 초기화되었습니다.")

    def close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._logger.info("Redis 연결이 종료되었습니다.")

    def create_collection(self, schema: CollectionSchema) -> None:
        self._ensure_client()
        schema = self._ensure_schema(schema)
        self._logger.info(f"Redis 컬렉션 준비: {schema.name}")

    def delete_collection(self, name: str) -> None:
        self._ensure_client()
        pattern = f"{name}:*"
        for key in self._scan_keys(pattern):
            self._client.delete(key)
        self._logger.info(f"Redis 컬렉션 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        schema = self._ensure_schema(schema, collection)
        if column.is_vector or column.name == schema.vector_field:
            if not self._enable_vector:
                raise RuntimeError("벡터 저장이 비활성화되었습니다.")
        return

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        payload_key = self._payload_storage_key(schema)
        targets = {payload_key, schema.vector_field}
        if column_name not in targets:
            return
        for key in self._scan_keys(f"{collection}:*"):
            self._client.hdel(key, column_name)

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        payload_key = self._payload_storage_key(schema)
        vector_key = schema.vector_field or "vector"
        for document in documents:
            payload = (
                json.dumps(document.payload)
                if schema.payload_field
                else json.dumps(document.fields)
            )
            vector = (
                json.dumps(document.vector.values)
                if document.vector and schema.vector_field
                else None
            )
            key = self._make_key(collection, document.doc_id)
            mapping: Dict[str, str] = {payload_key: payload}
            if vector is not None:
                mapping[vector_key] = vector
            self._client.hset(key, mapping=mapping)

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        key = self._make_key(collection, doc_id)
        data = self._client.hgetall(key)
        if not data:
            return None
        payload_key = self._payload_storage_key(schema)
        raw_payload = data.get(payload_key.encode(), b"{}").decode()
        payload_data = json.loads(raw_payload) if raw_payload else {}
        vector = self._parse_vector(data, schema)
        if schema.payload_field:
            return Document(doc_id=doc_id, fields={}, payload=payload_data, vector=vector)
        return Document(doc_id=doc_id, fields=payload_data, payload={}, vector=vector)

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_client()
        key = self._make_key(collection, doc_id)
        self._client.delete(key)

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        documents: List[Document] = []
        for key in self._scan_keys(f"{collection}:*"):
            doc_id = key.decode().split(":", 1)[1]
            document = self.get(collection, doc_id, schema)
            if document is None:
                continue
            if self._match_filter(document, query, schema):
                documents.append(document)
        if query.pagination:
            start = query.pagination.offset
            end = start + query.pagination.limit
            return documents[start:end]
        return documents

    def vector_search(
        self, request: VectorSearchRequest, schema: Optional[CollectionSchema] = None
    ) -> VectorSearchResponse:
        self._ensure_client()
        schema = self._ensure_schema(schema, request.collection)
        if not schema.vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        if not self._enable_vector:
            raise RuntimeError("벡터 검색이 비활성화되었습니다.")
        if request.filter_expression:
            raise NotImplementedError("Redis 벡터 검색 필터는 아직 지원하지 않습니다.")
        scored: List[Tuple[Document, float]] = []
        for key in self._scan_keys(f"{request.collection}:*"):
            doc_id = key.decode().split(":", 1)[1]
            document = self.get(request.collection, doc_id, schema)
            if document is None or document.vector is None:
                continue
            score = self._cosine_similarity(request.vector.values, document.vector.values)
            scored.append((document, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        items = scored[: request.top_k]
        if not request.include_vectors:
            for document, _ in items:
                document.vector = None
        return VectorSearchResponse(
            results=[
                VectorSearchResult(document=document, score=score)
                for document, score in items
            ],
            total=len(items),
        )

    def _ensure_client(self) -> None:
        if self._client is None:
            raise RuntimeError("Redis 연결이 초기화되지 않았습니다.")

    def _ensure_schema(
        self, schema: Optional[CollectionSchema], collection: Optional[str] = None
    ) -> CollectionSchema:
        if schema is not None:
            return schema
        if collection is None:
            raise ValueError("컬렉션 이름이 필요합니다.")
        return CollectionSchema.default(collection)

    def _payload_storage_key(self, schema: CollectionSchema) -> str:
        return schema.payload_field or "fields"

    def _make_key(self, collection: str, doc_id: object) -> str:
        return f"{collection}:{doc_id}"

    def _scan_keys(self, pattern: str) -> List[bytes]:
        cursor = 0
        keys: List[bytes] = []
        while True:
            cursor, batch = self._client.scan(cursor=cursor, match=pattern, count=200)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys

    def _parse_vector(self, data: Dict[bytes, bytes], schema: CollectionSchema) -> Optional[Vector]:
        if not schema.vector_field:
            return None
        vector_raw = data.get(schema.vector_field.encode())
        if not vector_raw:
            return None
        values = json.loads(vector_raw.decode())
        return Vector(values=values, dimension=len(values))

    def _match_filter(self, document: Document, query: Query, schema: CollectionSchema) -> bool:
        if not query.filter_expression or not query.filter_expression.conditions:
            return True
        logic = query.filter_expression.logic
        results = [
            self._evaluate_condition(document, condition, schema)
            for condition in query.filter_expression.conditions
        ]
        if logic == "OR":
            return any(results)
        return all(results)

    def _evaluate_condition(self, document: Document, condition, schema: CollectionSchema) -> bool:
        source = self._resolve_source(condition.source, condition.field, schema)
        if source == FieldSource.PAYLOAD:
            value = document.payload.get(condition.field)
        else:
            value = document.fields.get(condition.field)
        operator = condition.operator.value
        target = condition.value
        if operator == "EQ":
            return value == target
        if operator == "NE":
            return value != target
        if operator == "GT":
            return self._compare(value, target, lambda a, b: a > b)
        if operator == "GTE":
            return self._compare(value, target, lambda a, b: a >= b)
        if operator == "LT":
            return self._compare(value, target, lambda a, b: a < b)
        if operator == "LTE":
            return self._compare(value, target, lambda a, b: a <= b)
        if operator == "IN":
            return value in target if isinstance(target, list) else False
        if operator == "NOT_IN":
            return value not in target if isinstance(target, list) else False
        if operator == "CONTAINS":
            return self._contains(value, target)
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _resolve_source(
        self, source: FieldSource, field: str, schema: CollectionSchema
    ) -> FieldSource:
        if source != FieldSource.AUTO:
            return source
        if field in {schema.primary_key, schema.vector_field}:
            return FieldSource.COLUMN
        if schema.columns and field in schema.column_names():
            return FieldSource.COLUMN
        if not schema.payload_field:
            return FieldSource.COLUMN
        return FieldSource.PAYLOAD

    def _compare(self, left, right, func) -> bool:
        if left is None:
            return False
        try:
            return func(left, right)
        except TypeError:
            return False

    def _contains(self, value, target) -> bool:
        if value is None:
            return False
        if isinstance(value, list):
            return target in value
        if isinstance(value, str):
            return str(target) in value
        return False

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return float("-inf")
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return float("-inf")
        return dot / (norm_a * norm_b)
