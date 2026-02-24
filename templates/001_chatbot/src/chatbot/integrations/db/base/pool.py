"""
목적: DB 커넥션 풀 추상화를 제공한다.
설명: 커넥션 획득/반환 및 with 문 사용을 위한 인터페이스를 정의한다.
디자인 패턴: 오브젝트 풀
참조: src/rag_chatbot/integrations/db/base/session.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnectionPool(ABC):
    """커넥션 풀 인터페이스."""

    @abstractmethod
    def acquire(self) -> Any:
        """커넥션을 획득한다."""

    @abstractmethod
    def release(self, connection: Any) -> None:
        """커넥션을 반환한다."""
