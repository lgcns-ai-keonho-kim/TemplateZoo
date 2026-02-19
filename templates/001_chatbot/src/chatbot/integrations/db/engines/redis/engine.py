"""
목적: Redis 기반 DB 엔진을 제공한다.
설명: 스키마 기반 필드 저장과 간단한 검색을 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from chatbot.shared.logging import Logger, create_default_logger
from chatbot.integrations.db.base.engine import BaseDBEngine
from chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from chatbot.integrations.db.engines.sql_common import ensure_schema
from chatbot.integrations.db.engines.redis.connection import RedisConnectionManager
from chatbot.integrations.db.engines.redis.document_mapper import RedisDocumentMapper
from chatbot.integrations.db.engines.redis.filter_evaluator import (
    RedisFilterEvaluator,
)
from chatbot.integrations.db.engines.redis.keyspace import RedisKeyspaceHelper
from chatbot.integrations.db.engines.redis.vector_scorer import (
    RedisVectorScorer,
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
        self._logger = logger or create_default_logger("RedisEngine")
        self._enable_vector = enable_vector
        self._connection = RedisConnectionManager(url=url, logger=self._logger, redis_module=redis)
        self._keyspace = RedisKeyspaceHelper()
        self._document_mapper = RedisDocumentMapper(self._keyspace)
        self._filter_evaluator = RedisFilterEvaluator()
        self._vector_scorer = RedisVectorScorer()

    @property
    def name(self) -> str:
        return "redis"

    @property
    def supports_vector_search(self) -> bool:
        return self._enable_vector

    def connect(self) -> None:
        self._connection.connect()

    def close(self) -> None:
        self._connection.close()

    def create_collection(self, schema: CollectionSchema) -> None:
        self._connection.ensure_client()
        resolved_schema = ensure_schema(schema)
        self._logger.info(f"Redis 컬렉션 준비: {resolved_schema.name}")

    def delete_collection(self, name: str) -> None:
        client = self._connection.ensure_client()
        for key in self._keyspace.scan_keys(client, f"{name}:*"):
            client.delete(key)
        self._logger.info(f"Redis 컬렉션 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        if column.is_vector or column.name == resolved_schema.vector_field:
            if not self._enable_vector:
                raise RuntimeError("벡터 저장이 비활성화되었습니다.")
        return

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, collection)
        payload_key = self._keyspace.payload_storage_key(resolved_schema)
        targets = {payload_key, resolved_schema.vector_field}
        if column_name not in targets:
            return
        for key in self._keyspace.scan_keys(client, f"{collection}:*"):
            client.hdel(key, column_name)

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, collection)
        for document in documents:
            key = self._keyspace.make_key(collection, document.doc_id)
            mapping = self._document_mapper.to_hash_mapping(document, resolved_schema)
            client.hset(key, mapping=mapping)

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, collection)
        key = self._keyspace.make_key(collection, doc_id)
        data = client.hgetall(key)
        if not data:
            return None
        return self._document_mapper.from_hash(doc_id, data, resolved_schema)

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        client = self._connection.ensure_client()
        key = self._keyspace.make_key(collection, doc_id)
        client.delete(key)

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, collection)
        documents: List[Document] = []
        for key in self._keyspace.scan_keys(client, f"{collection}:*"):
            doc_id = key.decode().split(":", 1)[1]
            document = self.get(collection, doc_id, resolved_schema)
            if document is None:
                continue
            if self._filter_evaluator.match(document, query, resolved_schema):
                documents.append(document)
        if query.pagination:
            start = query.pagination.offset
            end = start + query.pagination.limit
            return documents[start:end]
        return documents

    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, request.collection)
        if not resolved_schema.vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        if not self._enable_vector:
            raise RuntimeError("벡터 검색이 비활성화되었습니다.")
        if request.filter_expression:
            raise NotImplementedError("Redis 벡터 검색 필터는 아직 지원하지 않습니다.")
        scored: List[Tuple[Document, float]] = []
        for key in self._keyspace.scan_keys(client, f"{request.collection}:*"):
            doc_id = key.decode().split(":", 1)[1]
            document = self.get(request.collection, doc_id, resolved_schema)
            if document is None or document.vector is None:
                continue
            score = self._vector_scorer.cosine_similarity(
                request.vector.values,
                document.vector.values,
            )
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
