"""
목적: MongoDB 기반 DB 엔진을 제공한다.
설명: 스키마 기반 필드 매핑과 기본 CRUD를 지원한다.
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
    Vector,
    VectorSearchRequest,
    VectorSearchResponse,
)

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - 환경 의존 로딩
    MongoClient = None


class MongoDBEngine(BaseDBEngine):
    """MongoDB 기반 엔진 구현체."""

    def __init__(
        self,
        uri: Optional[str] = None,
        database: str = "admin",
        host: str = "127.0.0.1",
        port: int = 27017,
        user: Optional[str] = None,
        password: Optional[str] = None,
        scheme: str = "mongodb",
        logger: Optional[Logger] = None,
    ) -> None:
        if not uri:
            auth = ""
            if user and password:
                auth = f"{user}:{password}@"
            elif user:
                auth = f"{user}@"
            elif password:
                auth = f":{password}@"
            uri = f"{scheme}://{auth}{host}:{port}"
        if not database:
            raise ValueError("database 설정이 필요합니다.")
        self._uri = uri
        self._database_name = database
        self._logger = logger or create_default_logger("MongoDBEngine")
        self._client: Optional[MongoClient] = None
        self._database = None

    @property
    def name(self) -> str:
        return "mongodb"

    @property
    def supports_vector_search(self) -> bool:
        return False

    def connect(self) -> None:
        if MongoClient is None:
            raise RuntimeError("pymongo 패키지가 설치되어 있지 않습니다.")
        if self._client is not None:
            return
        self._client = MongoClient(self._uri)
        self._database = self._client[self._database_name]
        self._logger.info("MongoDB 연결이 초기화되었습니다.")

    def close(self) -> None:
        if self._client is None:
            return
        self._client.close()
        self._client = None
        self._database = None
        self._logger.info("MongoDB 연결이 종료되었습니다.")

    def create_collection(self, schema: CollectionSchema) -> None:
        self._ensure_database()
        schema = self._ensure_schema(schema)
        if schema.name in self._database.list_collection_names():
            return
        self._database.create_collection(schema.name)
        self._logger.info(f"MongoDB 컬렉션 생성 완료: {schema.name}")

    def delete_collection(self, name: str) -> None:
        self._ensure_database()
        self._database.drop_collection(name)
        self._logger.info(f"MongoDB 컬렉션 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        schema = self._ensure_schema(schema, collection)
        if column.is_vector or column.name == schema.vector_field:
            raise RuntimeError("MongoDB 벡터 필드는 별도 설계가 필요합니다.")
        return

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_database()
        schema = self._ensure_schema(schema, collection)
        coll = self._database[collection]
        if schema.payload_field:
            field = f"{schema.payload_field}.{column_name}"
        else:
            field = column_name
        coll.update_many({}, {"$unset": {field: ""}})

    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_database()
        schema = self._ensure_schema(schema, collection)
        coll = self._database[collection]
        for document in documents:
            payload = {}
            if schema.payload_field:
                payload[schema.payload_field] = dict(document.payload)
            else:
                payload.update(document.fields)
            if schema.vector_field and document.vector:
                payload[schema.vector_field] = document.vector.values
            coll.update_one(
                {"_id": document.doc_id},
                {"$set": payload},
                upsert=True,
            )

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        self._ensure_database()
        schema = self._ensure_schema(schema, collection)
        coll = self._database[collection]
        data = coll.find_one({"_id": doc_id})
        if not data:
            return None
        payload = (
            data.get(schema.payload_field, {}) if schema.payload_field else {}
        )
        vector = None
        if schema.vector_field:
            raw_vector = data.get(schema.vector_field)
            if raw_vector is not None:
                vector = Vector(values=list(raw_vector), dimension=len(raw_vector))
        fields = {}
        if not schema.payload_field:
            fields = {
                key: value
                for key, value in data.items()
                if key not in {"_id", schema.vector_field}
            }
        return Document(
            doc_id=str(data["_id"]),
            fields=fields,
            payload=payload,
            vector=vector,
        )

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._ensure_database()
        coll = self._database[collection]
        coll.delete_one({"_id": doc_id})

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        self._ensure_database()
        schema = self._ensure_schema(schema, collection)
        coll = self._database[collection]
        filter_query = self._build_filter(query, schema)
        cursor = coll.find(filter_query)
        if query.pagination:
            cursor = cursor.skip(query.pagination.offset).limit(query.pagination.limit)
        documents: List[Document] = []
        for data in cursor:
            payload = (
                data.get(schema.payload_field, {}) if schema.payload_field else {}
            )
            vector = None
            if schema.vector_field:
                raw_vector = data.get(schema.vector_field)
                if raw_vector is not None:
                    vector = Vector(values=list(raw_vector), dimension=len(raw_vector))
            fields = {}
            if not schema.payload_field:
                fields = {
                    key: value
                    for key, value in data.items()
                    if key not in {"_id", schema.vector_field}
                }
            documents.append(
                Document(
                    doc_id=str(data["_id"]),
                    fields=fields,
                    payload=payload,
                    vector=vector,
                )
            )
        return documents

    def vector_search(
        self, request: VectorSearchRequest, schema: Optional[CollectionSchema] = None
    ) -> VectorSearchResponse:
        if schema and not schema.vector_field:
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        raise RuntimeError("MongoDB 벡터 검색은 비활성화되어 있습니다.")

    def _build_filter(self, query: Query, schema: CollectionSchema) -> dict:
        if not query.filter_expression or not query.filter_expression.conditions:
            return {}
        return self._build_filter_expression(query.filter_expression, schema)

    def _build_filter_expression(self, filter_expression, schema: CollectionSchema) -> dict:
        conditions = [
            self._condition_to_query(condition, schema)
            for condition in filter_expression.conditions
        ]
        if filter_expression.logic == "OR":
            return {"$or": conditions}
        return {"$and": conditions}

    def _condition_to_query(self, condition, schema: CollectionSchema) -> dict:
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
            return {field: value}
        if operator == "NE":
            return {field: {"$ne": value}}
        if operator == "GT":
            return {field: {"$gt": value}}
        if operator == "GTE":
            return {field: {"$gte": value}}
        if operator == "LT":
            return {field: {"$lt": value}}
        if operator == "LTE":
            return {field: {"$lte": value}}
        if operator == "IN":
            if not isinstance(value, list):
                raise ValueError("IN은 리스트 값이 필요합니다.")
            return {field: {"$in": value}}
        if operator == "NOT_IN":
            if not isinstance(value, list):
                raise ValueError("NOT_IN은 리스트 값이 필요합니다.")
            return {field: {"$nin": value}}
        if operator == "CONTAINS":
            if isinstance(value, str):
                return {field: {"$regex": value, "$options": "i"}}
            return {field: {"$in": [value]}}
        raise NotImplementedError("지원하지 않는 연산자입니다.")

    def _ensure_database(self) -> None:
        if self._database is None:
            raise RuntimeError("MongoDB 연결이 초기화되지 않았습니다.")

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
