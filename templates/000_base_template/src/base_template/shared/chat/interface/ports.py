"""
목적: Chat 실행 계층 공통 추상체를 정의한다.
설명: 그래프/서비스/실행기 인터페이스를 Protocol로 제공한다.
디자인 패턴: 포트-어댑터(Port/Protocol)
참조: src/base_template/shared/chat/services/chat_service.py, src/base_template/shared/chat/services/service_executor.py
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from typing import Any, Protocol, TypeAlias

StreamNodeConfig: TypeAlias = Mapping[str, str | Sequence[str]]


class GraphPort(Protocol):
    """Chat 그래프 실행 포트."""

    def compile(self, checkpointer: Any | None = None) -> Any:
        """그래프를 컴파일해 실행 객체를 반환한다."""

    def set_stream_node(self, stream_node: StreamNodeConfig) -> None:
        """스트림 노드 정책을 교체한다."""

    def invoke(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> str:
        """동기 실행 결과를 반환한다."""

    async def ainvoke(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> str:
        """비동기 실행 결과를 반환한다."""

    def stream_events(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """동기 스트림 이벤트를 반환한다."""

    def astream_events(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """비동기 스트림 이벤트를 반환한다."""


class ChatServicePort(Protocol):
    """Chat 서비스 실행 포트."""

    def close(self) -> None:
        """서비스 리소스를 정리한다."""

    def create_session(self, session_id: str | None = None, title: str | None = None) -> Any:
        """세션을 생성한다."""

    def list_sessions(self, limit: int, offset: int) -> list[Any]:
        """세션 목록을 조회한다."""

    def get_session(self, session_id: str) -> Any | None:
        """세션 1건을 조회한다."""

    def list_messages(self, session_id: str, limit: int, offset: int) -> list[Any]:
        """세션 메시지 목록을 조회한다."""

    def delete_session(self, session_id: str) -> None:
        """세션을 삭제한다."""

    def invoke(self, session_id: str, user_query: str, context_window: int = 20) -> Any:
        """동기 실행 결과를 반환한다."""

    async def ainvoke(self, session_id: str, user_query: str, context_window: int = 20) -> Any:
        """비동기 실행 결과를 반환한다."""

    def stream(
        self,
        session_id: str,
        user_query: str,
        context_window: int = 20,
    ) -> Iterator[dict[str, Any]]:
        """동기 스트림 이벤트를 반환한다."""

    def astream(
        self,
        session_id: str,
        user_query: str,
        context_window: int = 20,
    ) -> AsyncIterator[dict[str, Any]]:
        """비동기 스트림 이벤트를 반환한다."""


class ServiceExecutorPort(Protocol):
    """실행 오케스트레이터 포트."""

    def run_stream(self, session_id: str, user_query: str, context_window: int) -> Iterator[str]:
        """SSE 스트림을 생성한다."""
