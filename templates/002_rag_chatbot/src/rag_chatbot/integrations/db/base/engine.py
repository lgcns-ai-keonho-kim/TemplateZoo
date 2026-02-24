"""
목적: DB 엔진 추상 인터페이스를 정의한다.
설명: 컬렉션 관리, 문서 CRUD, 벡터 검색을 위한 표준 메서드를 제공한다.
디자인 패턴: 전략 패턴
참조: src/rag_chatbot/integrations/db/base/models.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from rag_chatbot.integrations.db.base.models import (
    CollectionSchema,
    ColumnSpec,
    Document,
    Query,
    VectorSearchRequest,
    VectorSearchResponse,
)


class BaseDBEngine(ABC):
    """DB 엔진 인터페이스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """엔진 이름을 반환한다."""

    @property
    @abstractmethod
    def supports_vector_search(self) -> bool:
        """벡터 검색 지원 여부를 반환한다."""

    @abstractmethod
    def connect(self) -> None:
        """DB 연결을 초기화한다."""

    @abstractmethod
    def close(self) -> None:
        """DB 연결을 종료한다."""

    @abstractmethod
    def create_collection(self, schema: CollectionSchema) -> None:
        """컬렉션을 생성한다."""

    @abstractmethod
    def delete_collection(self, name: str) -> None:
        """컬렉션을 삭제한다."""

    @abstractmethod
    def add_column(
        self,
        collection: str,
        column: ColumnSpec,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        """컬럼을 추가한다."""

    @abstractmethod
    def drop_column(
        self,
        collection: str,
        column_name: str,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        """컬럼을 삭제한다."""

    @abstractmethod
    def upsert(
        self,
        collection: str,
        documents: List[Document],
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        """문서를 삽입 또는 업데이트한다."""

    @abstractmethod
    def get(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> Optional[Document]:
        """단일 문서를 조회한다."""

    @abstractmethod
    def delete(
        self,
        collection: str,
        doc_id: object,
        schema: Optional[CollectionSchema] = None,
    ) -> None:
        """문서를 삭제한다."""

    @abstractmethod
    def query(
        self,
        collection: str,
        query: Query,
        schema: Optional[CollectionSchema] = None,
    ) -> List[Document]:
        """일반 조회를 수행한다."""

    @abstractmethod
    def vector_search(
        self,
        request: VectorSearchRequest,
        schema: Optional[CollectionSchema] = None,
    ) -> VectorSearchResponse:
        """벡터 검색을 수행한다."""
