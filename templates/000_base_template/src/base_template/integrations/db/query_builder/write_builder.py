"""
목적: 쓰기 전용 DSL 빌더를 제공한다.
설명: 업서트 중심의 간단한 쓰기 호출을 제공한다.
디자인 패턴: 파사드
참조: src/base_template/integrations/db/base/engine.py
"""

from __future__ import annotations

from typing import Optional, Sequence

from ..base.engine import BaseDBEngine
from ..base.models import CollectionSchema, Document


class WriteBuilder:
    """쓰기 DSL 빌더."""

    def __init__(
        self,
        engine: BaseDBEngine,
        collection: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        self._engine = engine
        self._collection = collection
        self._schema = schema

    def upsert(self, documents: Sequence[Document]) -> None:
        """문서를 업서트한다."""

        if self._schema:
            for document in documents:
                self._schema.validate_document(document)
        self._engine.upsert(self._collection, list(documents), self._schema)

    def upsert_one(self, document: Document) -> None:
        """단일 문서를 업서트한다."""

        if self._schema:
            self._schema.validate_document(document)
        self._engine.upsert(self._collection, [document], self._schema)
