"""
목적: 쓰기 전용 DSL 빌더를 제공한다.
설명: 업서트 중심의 간단한 쓰기 호출을 제공한다.
디자인 패턴: 파사드
참조: src/chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional, Sequence

from chatbot.integrations.db.base.engine import BaseDBEngine
from chatbot.integrations.db.base.models import CollectionSchema, Document


class WriteBuilder:
    """쓰기 DSL 빌더."""

    def __init__(
        self,
        engine: BaseDBEngine,
        collection: str,
        schema: Optional[CollectionSchema] = None,
        upsert_executor: Optional[
            Callable[[str, Sequence[Document], Optional[CollectionSchema]], None]
        ] = None,
    ) -> None:
        self._engine = engine
        self._collection = collection
        self._schema = schema
        self._upsert_executor = upsert_executor

    def upsert(self, documents: Sequence[Document]) -> None:
        """문서를 업서트한다."""

        if self._upsert_executor is not None:
            self._upsert_executor(self._collection, documents, self._schema)
            return
        if self._schema:
            for document in documents:
                self._schema.validate_document(document)
        self._engine.upsert(self._collection, list(documents), self._schema)

    def upsert_one(self, document: Document) -> None:
        """단일 문서를 업서트한다."""

        if self._upsert_executor is not None:
            self._upsert_executor(self._collection, [document], self._schema)
            return
        if self._schema:
            self._schema.validate_document(document)
        self._engine.upsert(self._collection, [document], self._schema)
