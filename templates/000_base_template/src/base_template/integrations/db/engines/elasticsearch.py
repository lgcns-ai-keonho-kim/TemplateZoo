"""
목적: Elasticsearch 기반 DB 엔진을 제공한다.
설명: 스키마 기반 필드 매핑과 벡터 검색을 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/integrations/db/base/engine.py
"""

from __future__ import annotations

from typing import List, Optional

from ....shared.logging import Logger, create_default_logger
from ..base.engine import BaseDBEngine
from ..base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    FieldSource,
    Query,
    SortOrder,
    Vector,
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
)

try:
    from elasticsearch import Elasticsearch
except ImportError:  # pragma: no cover - 환경 의존 로딩
    Elasticsearch = None


class ElasticSearchEngine(BaseDBEngine):
    """Elasticsearch 기반 엔진 구현체."""

    def __init__(
        self,
        hosts: Optional[List[str]] = None,
        host: str = "127.0.0.1",
        port: int = 9200,
        scheme: str = "http",
        user: Optional[str] = None,
        password: Optional[str] = None,
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
        self._hosts = hosts
        self._logger = logger or create_default_logger("ElasticSearchEngine")
        self._client: Optional[Elasticsearch] = None

    @property
    def name(self) -> str:
        return "elasticsearch"

    @property
    def supports_vector_search(self) -> bool:
        return True

    def connect(self) -> None:
        if Elasticsearch is None:
            raise RuntimeError("elasticsearch 패키지가 설치되어 있지 않습니다.")
        if self._client is not None:
            return
        self._client = Elasticsearch(self._hosts)
        self._logger.info("Elasticsearch 연결이 초기화되었습니다.")

    def close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._logger.info("Elasticsearch 연결이 종료되었습니다.")

    def create_collection(self, schema: CollectionSchema) -> None:
        self._ensure_client()
        schema = self._ensure_schema(schema)
        mappings = {"properties": {}}
        if schema.payload_field:
            mappings["properties"][schema.payload_field] = {"type": "object"}
        if schema.vector_field:
            vector_dim = schema.resolve_vector_dimension()
            if vector_dim is None:
                raise ValueError("벡터 차원 정보가 필요합니다.")
            mappings["properties"][schema.vector_field] = {
                "type": "dense_vector",
                "dims": vector_dim,
                "index": True,
                "similarity": "cosine",
            }
        self._client.indices.create(index=schema.name, mappings=mappings, ignore=400)
        self._logger.info(f"Elasticsearch 인덱스 생성 완료: {schema.name}")

    def delete_collection(self, name: str) -> None:
        self._ensure_client()
        self._client.indices.delete(index=name, ignore=[400, 404])
        self._logger.info(f"Elasticsearch 인덱스 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        properties: dict = {}
        if column.is_vector or column.name == schema.vector_field:
            vector_dim = schema.resolve_vector_dimension()
            if vector_dim is None:
                raise ValueError("벡터 차원 정보가 필요합니다.")
            properties[column.name] = {
                "type": "dense_vector",
                "dims": vector_dim,
                "index": True,
                "similarity": "cosine",
            }
        elif schema.payload_field and column.name == schema.payload_field:
            properties[column.name] = {"type": "object"}
        else:
            properties[column.name] = {"type": column.data_type or "keyword"}
        self._client.indices.put_mapping(index=schema.name, properties=properties)

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
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        for document in documents:
            body = {}
            if schema.payload_field:
                body[schema.payload_field] = document.payload
            else:
                body.update(document.fields)
            if schema.vector_field and document.vector:
                body[schema.vector_field] = document.vector.values
            self._client.index(index=collection, id=document.doc_id, document=body)

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        response = self._client.get(index=collection, id=doc_id, ignore=[404])
        if response.get("found") is False:
            return None
        source = response.get("_source", {})
        payload = (
            source.get(schema.payload_field, {}) if schema.payload_field else {}
        )
        vector = None
        if schema.vector_field:
            raw_vector = source.get(schema.vector_field)
            if raw_vector is not None:
                vector = Vector(values=raw_vector, dimension=len(raw_vector))
        return Document(doc_id=doc_id, fields={}, payload=payload, vector=vector)

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_client()
        self._client.delete(index=collection, id=doc_id, ignore=[404])

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        self._ensure_client()
        schema = self._ensure_schema(schema, collection)
        body = {"query": {"match_all": {}}}
        filter_query = self._build_filter(query, schema)
        if filter_query:
            body["query"] = filter_query
        if query.sort:
            sort_clauses = []
            for sort_field in query.sort:
                order = "asc" if sort_field.order == SortOrder.ASC else "desc"
                source = self._resolve_source(sort_field.source, sort_field.field, schema)
                if source == FieldSource.PAYLOAD:
                    sort_field_name = f"{schema.payload_field}.{sort_field.field}"
                else:
                    sort_field_name = sort_field.field
                sort_clauses.append({sort_field_name: {"order": order}})
            body["sort"] = sort_clauses
        if query.pagination:
            body["from"] = query.pagination.offset
            body["size"] = query.pagination.limit
        response = self._client.search(index=collection, body=body)
        hits = response.get("hits", {}).get("hits", [])
        documents: List[Document] = []
        for hit in hits:
            source = hit.get("_source", {})
            payload = (
                source.get(schema.payload_field, {}) if schema.payload_field else {}
            )
            vector = None
            if schema.vector_field:
                raw_vector = source.get(schema.vector_field)
                if raw_vector is not None:
                    vector = Vector(values=raw_vector, dimension=len(raw_vector))
            documents.append(
                Document(
                    doc_id=hit.get("_id"),
                    fields={},
                    payload=payload,
                    vector=vector,
                )
            )
        return documents

    def vector_search(
        self, request: VectorSearchRequest, schema: Optional[CollectionSchema] = None
    ) -> VectorSearchResponse:
        self._ensure_client()
        schema = self._ensure_schema(schema, request.collection)
        if not schema.vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        knn_body = {
            "field": schema.vector_field,
            "query_vector": request.vector.values,
            "k": request.top_k,
            "num_candidates": max(request.top_k * 2, 10),
        }
        filter_query = self._build_filter_expression(request.filter_expression, schema)
        if filter_query:
            knn_body["filter"] = filter_query
        body = {"knn": knn_body}
        response = self._client.search(index=request.collection, body=body)
        hits = response.get("hits", {}).get("hits", [])
        results: List[VectorSearchResult] = []
        for hit in hits:
            source = hit.get("_source", {})
            payload = (
                source.get(schema.payload_field, {}) if schema.payload_field else {}
            )
            vector = None
            if request.include_vectors and schema.vector_field:
                raw_vector = source.get(schema.vector_field)
                if raw_vector is not None:
                    vector = Vector(values=raw_vector, dimension=len(raw_vector))
            document = Document(
                doc_id=hit.get("_id"),
                fields={},
                payload=payload,
                vector=vector,
            )
            results.append(
                VectorSearchResult(document=document, score=float(hit.get("_score", 0.0)))
            )
        return VectorSearchResponse(results=results, total=len(results))

    def _build_filter(self, query: Query, schema: CollectionSchema) -> Optional[dict]:
        if not query.filter_expression or not query.filter_expression.conditions:
            return None
        return self._build_filter_expression(query.filter_expression, schema)

    def _build_filter_expression(self, filter_expression, schema: CollectionSchema) -> Optional[dict]:
        if filter_expression is None or not filter_expression.conditions:
            return None
        must = []
        should = []
        must_not = []
        for condition in filter_expression.conditions:
            positive, negative = self._condition_to_query(condition, schema)
            if positive:
                if filter_expression.logic == "OR":
                    should.append(positive)
                else:
                    must.append(positive)
            if negative:
                must_not.append(negative)
        bool_query: dict = {}
        if must:
            bool_query["must"] = must
        if should:
            bool_query["should"] = should
            bool_query["minimum_should_match"] = 1
        if must_not:
            bool_query["must_not"] = must_not
        return {"bool": bool_query} if bool_query else None

    def _condition_to_query(self, condition, schema: CollectionSchema) -> tuple[Optional[dict], Optional[dict]]:
        source = self._resolve_source(condition.source, condition.field, schema)
        if source == FieldSource.PAYLOAD:
            if not schema.payload_field:
                raise RuntimeError("payload 필드가 정의되어 있지 않습니다.")
            field = f"{schema.payload_field}.{condition.field}"
        else:
            field = condition.field
        operator = condition.operator.value
        value = condition.value
        if operator == "EQ":
            return {"term": {field: value}}, None
        if operator == "NE":
            return None, {"term": {field: value}}
        if operator in {"GT", "GTE", "LT", "LTE"}:
            op_map = {"GT": "gt", "GTE": "gte", "LT": "lt", "LTE": "lte"}
            return {"range": {field: {op_map[operator]: value}}}, None
        if operator == "IN":
            if not isinstance(value, list):
                raise ValueError("IN은 리스트 값이 필요합니다.")
            return {"terms": {field: value}}, None
        if operator == "NOT_IN":
            if not isinstance(value, list):
                raise ValueError("NOT_IN은 리스트 값이 필요합니다.")
            return None, {"terms": {field: value}}
        if operator == "CONTAINS":
            return {"wildcard": {field: f"*{value}*"}}, None
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _ensure_client(self) -> None:
        if self._client is None:
            raise RuntimeError("Elasticsearch 연결이 초기화되지 않았습니다.")

    def _ensure_schema(
        self, schema: Optional[CollectionSchema], collection: Optional[str] = None
    ) -> CollectionSchema:
        if schema is not None:
            return schema
        if collection is None:
            raise ValueError("컬렉션 이름이 필요합니다.")
        return CollectionSchema.default(collection)

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
