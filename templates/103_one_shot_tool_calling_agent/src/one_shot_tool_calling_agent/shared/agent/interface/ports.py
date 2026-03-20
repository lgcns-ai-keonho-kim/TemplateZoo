"""
목적: Agent 실행 계층 공통 추상체를 정의한다.
설명: 그래프 인터페이스를 Protocol로 제공한다.
디자인 패턴: 포트-어댑터(Port/Protocol)
참조: src/one_shot_tool_calling_agent/shared/agent/services/agent_service.py
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from typing import Any, Protocol, TypeAlias

StreamNodeConfig: TypeAlias = Mapping[str, str | Sequence[str]]


class GraphPort(Protocol):
    """Agent 그래프 실행 포트."""

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
