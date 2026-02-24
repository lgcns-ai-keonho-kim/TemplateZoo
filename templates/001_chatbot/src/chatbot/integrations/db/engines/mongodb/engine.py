"""
목적: MongoDB 기반 DB 엔진을 제공한다.
설명: 스키마 기반 필드 매핑과 기본 CRUD를 지원한다.
디자인 패턴: 어댑터 패턴
참조: src/chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

from typing import Any, Optional

from chatbot.shared.logging import Logger, create_default_logger
from chatbot.integrations.db.base.engine import BaseDBEngine
from chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
)
from chatbot.integrations.db.engines.sql_common import ensure_schema
from chatbot.integrations.db.engines.mongodb.connection import MongoConnectionManager
from chatbot.integrations.db.engines.mongodb.document_mapper import MongoDocumentMapper
from chatbot.integrations.db.engines.mongodb.filter_builder import (
    MongoFilterBuilder,
)
from chatbot.integrations.db.engines.mongodb.schema_manager import MongoSchemaManager

MongoClient: Any | None
try:
    from pymongo import MongoClient as _MongoClient
except ImportError:  # pragma: no cover - 환경 의존 로딩
    MongoClient = None
else:  # pragma: no cover - 환경 의존 로딩
    MongoClient = _MongoClient


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
        auth_source: Optional[str] = None,
        scheme: str = "mongodb",
        logger: Optional[Logger] = None,
    ) -> None:
        auth_source = self._normalize_auth_source(auth_source)
        if auth_source is None and (user or password) and database:
            auth_source = database
        if not uri:
            auth = ""
            if user and password:
                auth = f"{user}:{password}@"
            elif user:
                auth = f"{user}@"
            elif password:
                auth = f":{password}@"
            uri = f"{scheme}://{auth}{host}:{port}"
            if auth_source and (user or password):
                uri = f"{uri}/?authSource={auth_source}"
        if not database:
            raise ValueError("database 설정이 필요합니다.")
        self._database_name = database
        self._logger = logger or create_default_logger("MongoDBEngine")
        self._connection = MongoConnectionManager(
            uri=uri,
            database_name=database,
            auth_source=auth_source,
            logger=self._logger,
            mongo_client_cls=MongoClient,
        )
        self._schema_manager = MongoSchemaManager()
        self._filter_builder = MongoFilterBuilder()
        self._document_mapper = MongoDocumentMapper()

    @property
    def name(self) -> str:
        return "mongodb"

    @property
    def supports_vector_search(self) -> bool:
        return False

    def connect(self) -> None:
        self._connection.connect()

    def close(self) -> None:
        self._connection.close()

    def create_collection(self, schema: CollectionSchema) -> None:
        database = self._connection.ensure_database()
        resolved_schema = ensure_schema(schema)
        self._schema_manager.create_collection(database, resolved_schema)
        self._logger.info(f"MongoDB 컬렉션 생성 완료: {resolved_schema.name}")

    def delete_collection(self, name: str) -> None:
        database = self._connection.ensure_database()
        self._schema_manager.delete_collection(database, name)
        self._logger.info(f"MongoDB 컬렉션 삭제 완료: {name}")

    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        resolved_schema = ensure_schema(schema, collection)
        self._schema_manager.add_column(resolved_schema, column)
        return

    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        database = self._connection.ensure_database()
        resolved_schema = ensure_schema(schema, collection)
        self._schema_manager.drop_column(
            database=database,
            collection=collection,
            schema=resolved_schema,
            column_name=column_name,
        )

    def upsert(
        self,
        collection: str,
        documents: list[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        database = self._connection.ensure_database()
        resolved_schema = ensure_schema(schema, collection)
        coll = database[collection]
        for document in documents:
            payload = self._document_mapper.to_update_payload(document, resolved_schema)
            coll.update_one({"_id": document.doc_id}, {"$set": payload}, upsert=True)

    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        database = self._connection.ensure_database()
        resolved_schema = ensure_schema(schema, collection)
        coll = database[collection]
        data = coll.find_one({"_id": doc_id})
        if not data:
            return None
        return self._document_mapper.from_record(data, resolved_schema)

    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        database = self._connection.ensure_database()
        coll = database[collection]
        coll.delete_one({"_id": doc_id})

    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> list[Document]:
        database = self._connection.ensure_database()
        resolved_schema = ensure_schema(schema, collection)
        coll = database[collection]
        filter_query = self._filter_builder.build(query.filter_expression, resolved_schema)
        cursor = coll.find(filter_query)
        if query.pagination:
            cursor = cursor.skip(query.pagination.offset).limit(query.pagination.limit)
        return [
            self._document_mapper.from_record(data, resolved_schema)
            for data in cursor
        ]

    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        if schema and not (request.vector_field or schema.vector_field):
            raise RuntimeError("벡터 필드가 정의되어 있지 않습니다.")
        raise RuntimeError("MongoDB 벡터 검색은 비활성화되어 있습니다.")

    def _normalize_auth_source(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        return trimmed
