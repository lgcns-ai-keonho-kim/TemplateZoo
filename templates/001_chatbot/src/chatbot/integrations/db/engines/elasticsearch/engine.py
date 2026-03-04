"""
목적: Elasticsearch 기반 DB 엔진을 제공한다.
설명: 스키마 기반 필드 매핑과 벡터 검색을 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

from typing import Any, List, Optional

from chatbot.shared.logging import Logger, create_default_logger
from chatbot.integrations.db.base.engine import BaseDBEngine
from chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    Query,
    SortOrder,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)
from chatbot.integrations.db.engines.sql_common import ensure_schema
from chatbot.integrations.db.engines.elasticsearch.connection import (
    ElasticConnectionManager,
)
from chatbot.integrations.db.engines.elasticsearch.document_mapper import (
    ElasticDocumentMapper,
)
from chatbot.integrations.db.engines.elasticsearch.filter_builder import (
    ElasticFilterBuilder,
)
from chatbot.integrations.db.engines.elasticsearch.schema_manager import (
    ElasticSchemaManager,
)

Elasticsearch: Any | None
try:
    from elasticsearch import Elasticsearch as _Elasticsearch
except ImportError:  # pragma: no cover - 환경 의존 로딩
    Elasticsearch = None
else:  # pragma: no cover - 환경 의존 로딩
    Elasticsearch = _Elasticsearch


class ElasticsearchEngine(BaseDBEngine):
    """Elasticsearch 기반 엔진 구현체."""

    def __init__(
        self,
        hosts: Optional[List[str]] = None,
        host: str = "127.0.0.1",
        port: int = 9200,
        scheme: str = "http",
        user: Optional[str] = None,
        password: Optional[str] = None,
        ca_certs: Optional[str] = None,
        verify_certs: Optional[bool] = None,
        ssl_assert_fingerprint: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        if not hosts:
            auth = ""
            if user and password:
                auth = f"{user}:{password}@"
            elif user:
                auth = f"{user}@"
            elif password:
                auth = f":{password}@"
            hosts = [f"{scheme}://{auth}{host}:{port}"]
        self._logger = logger or create_default_logger("ElasticsearchEngine")
        self._connection = ElasticConnectionManager(
            hosts=hosts,
            logger=self._logger,
            elasticsearch_cls=Elasticsearch,
            ca_certs=ca_certs,
            verify_certs=verify_certs,
            ssl_assert_fingerprint=ssl_assert_fingerprint,
        )
        self._schema_manager = ElasticSchemaManager()
        self._filter_builder = ElasticFilterBuilder()
        self._document_mapper = ElasticDocumentMapper()

    @property
    def name(self) -> str:
        return "elasticsearch"

    @property
    def supports_vector_search(self) -> bool:
        return True

    def connect(self) -> None:
        self._connection.connect()

    def close(self) -> None:
        self._connection.close()

    def create_collection(self, schema: CollectionSchema) -> None:
        resolved_schema = ensure_schema(schema)
        client = self._connection.with_options(ignore_status=400)
        self._schema_manager.create_collection(client, resolved_schema)
        self._logger.info(f"Elasticsearch 인덱스 생성 완료: {resolved_schema.name}")

    def delete_collection(self, name: str) -> None:
        client = self._connection.with_options(ignore_status=[400, 404])
        self._schema_manager.delete_collection(client, name)
        self._logger.info(f"Elasticsearch 인덱스 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        client = self._connection.ensure_client()
        self._schema_manager.add_column(client, resolved_schema, column)

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        raise RuntimeError("Elasticsearch는 컬럼 삭제를 지원하지 않습니다. reindex가 필요합니다.")

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, collection)
        for document in documents:
            body = self._document_mapper.to_index_document(document, resolved_schema)
            client.index(index=collection, id=document.doc_id, document=body)

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        resolved_schema = ensure_schema(schema, collection)
        client = self._connection.with_options(ignore_status=[404])
        response = client.get(index=collection, id=doc_id)
        if response.get("found") is False:
            return None
        return self._document_mapper.from_hit(
            {"_id": doc_id, "_source": response.get("_source", {})},
            resolved_schema,
            include_vector=True,
        )

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        client = self._connection.with_options(ignore_status=[404])
        client.delete(index=collection, id=doc_id)

    def refresh_collection(self, name: str) -> None:
        """검색 일관성을 위해 인덱스를 강제로 리프레시한다."""

        client = self._connection.ensure_client()
        client.indices.refresh(index=name)

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, collection)
        body = {"query": {"match_all": {}}}
        filter_query = self._filter_builder.build(query.filter_expression, resolved_schema)
        if filter_query:
            body["query"] = filter_query
        if query.sort:
            sort_clauses = []
            for sort_field in query.sort:
                order = "asc" if sort_field.order == SortOrder.ASC else "desc"
                source = resolved_schema.resolve_source(sort_field.field, sort_field.source)
                if source == FieldSource.PAYLOAD:
                    sort_field_name = f"{resolved_schema.payload_field}.{sort_field.field}"
                else:
                    sort_field_name = sort_field.field
                sort_clauses.append({sort_field_name: {"order": order}})
            body["sort"] = sort_clauses
        if query.pagination:
            body["from"] = query.pagination.offset
            body["size"] = query.pagination.limit
        response = client.search(index=collection, body=body)
        hits = response.get("hits", {}).get("hits", [])
        return [
            self._document_mapper.from_hit(hit, resolved_schema, include_vector=True)
            for hit in hits
        ]

    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        client = self._connection.ensure_client()
        resolved_schema = ensure_schema(schema, request.collection)
        target_vector_field = request.vector_field or resolved_schema.vector_field
        if not target_vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        knn_body = {
            "field": target_vector_field,
            "query_vector": request.vector.values,
            "k": request.top_k,
            "num_candidates": max(request.top_k * 2, 10),
        }
        filter_query = self._filter_builder.build(
            request.filter_expression,
            resolved_schema,
        )
        if filter_query:
            knn_body["filter"] = filter_query
        body = {"knn": knn_body}
        response = client.search(index=request.collection, body=body)
        hits = response.get("hits", {}).get("hits", [])
        results = [
            VectorSearchResult(
                document=self._document_mapper.from_hit(
                    hit,
                    resolved_schema,
                    include_vector=request.include_vectors,
                ),
                score=float(hit.get("_score", 0.0)),
            )
            for hit in hits
        ]
        return VectorSearchResponse(results=results, total=len(results))
