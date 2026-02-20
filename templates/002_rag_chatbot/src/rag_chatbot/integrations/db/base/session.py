"""
목적: DB 세션/트랜잭션 추상화를 제공한다.
설명: 트랜잭션 제어와 with 문 사용을 위한 인터페이스를 정의한다.
디자인 패턴: 템플릿 메서드, 컨텍스트 매니저
참조: src/rag_chatbot/integrations/db/base/engine.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseSession(ABC):
    """DB 세션 인터페이스."""

    @abstractmethod
    def begin(self) -> None:
        """트랜잭션을 시작한다."""

    @abstractmethod
    def commit(self) -> None:
        """트랜잭션을 커밋한다."""

    @abstractmethod
    def rollback(self) -> None:
        """트랜잭션을 롤백한다."""

    def __enter__(self) -> "BaseSession":
        self.begin()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
