"""
목적: 파일 시스템 엔진 인터페이스를 제공한다.
설명: 파일 쓰기/읽기/목록/이동/복사를 위한 표준 메서드를 정의한다.
디자인 패턴: 전략 패턴
참조: src/rag_chatbot/integrations/fs/engines/local.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseFSEngine(ABC):
    """파일 시스템 엔진 인터페이스."""

    @property
    @abstractmethod
    def name(self) -> str:
        """엔진 이름을 반환한다."""

    @abstractmethod
    def write_text(self, path: str, content: str, encoding: str) -> None:
        """파일에 텍스트를 기록한다."""

    @abstractmethod
    def read_text(self, path: str, encoding: str) -> str:
        """파일에서 텍스트를 읽는다."""

    @abstractmethod
    def list_files(
        self,
        base_dir: str,
        recursive: bool = False,
        suffix: Optional[str] = None,
    ) -> List[str]:
        """파일 목록을 반환한다."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """경로 존재 여부를 반환한다."""

    @abstractmethod
    def mkdir(self, path: str, exist_ok: bool = True) -> None:
        """디렉터리를 생성한다."""

    @abstractmethod
    def move(self, src: str, dst: str) -> None:
        """파일/디렉터리를 이동한다."""

    @abstractmethod
    def copy(self, src: str, dst: str) -> None:
        """파일을 복사한다."""
