"""
목적: 공통 예외 베이스 클래스를 제공한다.
설명: 메시지를 외부에서 주입받고, Pydantic 기반 상세 모델과 함께 보관한다.
디자인 패턴: 도메인 예외 객체
참조: src/rag_chatbot/shared/exceptions/models.py
"""

from __future__ import annotations

from typing import Optional

from rag_chatbot.shared.exceptions.models import ExceptionDetail


class BaseAppException(Exception):
    """애플리케이션 공통 예외 클래스이다.

    Args:
        message: 사용자 또는 시스템에 전달할 메시지.
        detail: 예외 상세 정보 모델.
        original: 원본 예외 객체.
    """

    def __init__(
        self,
        message: str,
        detail: ExceptionDetail,
        original: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self._message = message
        self._detail = detail
        self._original = original

    @property
    def message(self) -> str:
        """주입된 메시지를 반환한다."""

        return self._message

    @property
    def detail(self) -> ExceptionDetail:
        """예외 상세 모델을 반환한다."""

        return self._detail

    @property
    def original(self) -> Optional[Exception]:
        """원본 예외를 반환한다."""

        return self._original

    def to_dict(self) -> dict:
        """예외 정보를 사전으로 변환한다."""

        return {
            "message": self._message,
            "detail": self._detail.model_dump(),
            "original": repr(self._original) if self._original else None,
        }

