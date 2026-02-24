"""
목적: 삭제 전용 DSL 빌더를 제공한다.
설명: ID 삭제와 QueryBuilder 기반 다건 삭제를 지원한다.
디자인 패턴: 파사드
참조: src/chatbot/integrations/db/base/query_builder.py
"""

from __future__ import annotations

from collections.abc import Callable
from typing import List, Optional

from chatbot.integrations.db.base.engine import BaseDBEngine
from chatbot.integrations.db.base.models import (
    CollectionSchema,
    Document,
    FieldSource,
    Query,
)
from chatbot.integrations.db.base.query_builder import QueryBuilder


class DeleteBuilder:
    """삭제 DSL 빌더."""

    def __init__(
        self,
        engine: BaseDBEngine,
        collection: str,
        schema: Optional[CollectionSchema] = None,
        query_executor: Optional[
            Callable[[str, Query, Optional[CollectionSchema]], List[Document]]
        ] = None,
        delete_executor: Optional[
            Callable[[str, object, Optional[CollectionSchema]], None]
        ] = None,
    ) -> None:
        self._engine = engine
        self._collection = collection
        self._builder = QueryBuilder()
        self._schema = schema
        self._query_executor = query_executor
        self._delete_executor = delete_executor

    def by_id(self, doc_id: object) -> None:
        """ID로 삭제한다."""

        if self._delete_executor is not None:
            self._delete_executor(self._collection, doc_id, self._schema)
            return
        self._engine.delete(self._collection, doc_id, self._schema)

    def by_ids(self, doc_ids: List[object]) -> None:
        """여러 ID를 삭제한다."""

        for doc_id in doc_ids:
            if self._delete_executor is not None:
                self._delete_executor(self._collection, doc_id, self._schema)
                continue
            self._engine.delete(self._collection, doc_id, self._schema)

    def where(
        self, field: str, source: FieldSource = FieldSource.AUTO
    ) -> "DeleteBuilder":
        self._builder.where(field, source)
        return self

    def where_column(self, field: str) -> "DeleteBuilder":
        self._builder.where_column(field)
        return self

    def where_payload(self, field: str) -> "DeleteBuilder":
        self._builder.where_payload(field)
        return self

    def and_(self) -> "DeleteBuilder":
        self._builder.and_()
        return self

    def or_(self) -> "DeleteBuilder":
        self._builder.or_()
        return self

    def eq(self, value: object) -> "DeleteBuilder":
        self._builder.eq(value)
        return self

    def ne(self, value: object) -> "DeleteBuilder":
        self._builder.ne(value)
        return self

    def gt(self, value: object) -> "DeleteBuilder":
        self._builder.gt(value)
        return self

    def gte(self, value: object) -> "DeleteBuilder":
        self._builder.gte(value)
        return self

    def lt(self, value: object) -> "DeleteBuilder":
        self._builder.lt(value)
        return self

    def lte(self, value: object) -> "DeleteBuilder":
        self._builder.lte(value)
        return self

    def in_(self, values: List[object]) -> "DeleteBuilder":
        self._builder.in_(values)
        return self

    def not_in(self, values: List[object]) -> "DeleteBuilder":
        self._builder.not_in(values)
        return self

    def contains(self, value: object) -> "DeleteBuilder":
        self._builder.contains(value)
        return self

    def execute(self) -> int:
        """조건에 맞는 문서를 조회 후 삭제한다."""

        query = self._builder.build()
        return self._delete_by_query(query)

    def delete_by_query(self, query: Query) -> int:
        """Query로 문서를 조회 후 삭제한다."""

        return self._delete_by_query(query)

    def _delete_by_query(self, query: Query) -> int:
        if self._query_executor is not None:
            documents = self._query_executor(self._collection, query, self._schema)
        else:
            if self._schema:
                self._schema.validate_query(query)
            documents = self._engine.query(self._collection, query, self._schema)
        for document in documents:
            if self._delete_executor is not None:
                self._delete_executor(self._collection, document.doc_id, self._schema)
                continue
            self._engine.delete(self._collection, document.doc_id, self._schema)
        return len(documents)
