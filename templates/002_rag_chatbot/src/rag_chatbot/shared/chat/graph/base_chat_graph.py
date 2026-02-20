"""
목적: Chat 그래프 공통 실행 구현체를 제공한다.
설명: 그래프 컴파일/실행/이벤트 표준화/스트림 노드 정책 필터를 공통화한다.
디자인 패턴: 합성(Builder 주입)
참조: src/rag_chatbot/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict

from rag_chatbot.shared.chat.interface import StreamNodeConfig
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger


class DefaultChatGraphInput(BaseModel):
    """기본 그래프 입력 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    user_message: str
    history: list[Any]
    assistant_message: str = ""


class BaseChatGraph:
    """Builder 주입형 Chat 그래프 실행 구현체."""

    def __init__(
        self,
        *,
        builder: Any,
        checkpointer: object | None = None,
        stream_node: StreamNodeConfig | None = None,
        logger: Logger | None = None,
        input_model: type[BaseModel] | None = None,
    ) -> None:
        self._logger = logger or create_default_logger("BaseChatGraph")
        self._builder = builder
        self._input_model = input_model or DefaultChatGraphInput
        self._compiled_graph: Any | None = None
        self._stream_node: dict[str, set[str]] = {}
        self.set_stream_node(stream_node or {})
        self.compile(checkpointer=checkpointer)

    def set_stream_node(self, stream_node: StreamNodeConfig) -> None:
        """스트림 노드 정책을 교체한다."""

        self._stream_node = self._normalize_stream_node(stream_node)

    def compile(self, checkpointer: object | None = None) -> Any:
        """그래프를 컴파일해 내부에 보관하고 반환한다."""

        self._compiled_graph = self._builder.compile(checkpointer=checkpointer)
        return self._compiled_graph

    def invoke(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> str:
        """그래프를 동기 실행해 최종 답변 문자열을 반환한다."""

        result = self._require_compiled().invoke(
            self._build_input(session_id, user_message, history),
            config=self._merge_config(session_id, config),
        )
        content = self._extract_assistant_message(result)
        if content:
            return content
        detail = ExceptionDetail(
            code="CHAT_STREAM_EMPTY",
            cause="BaseChatGraph.invoke produced empty assistant_message",
        )
        raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)

    async def ainvoke(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> str:
        """그래프를 비동기 실행해 최종 답변 문자열을 반환한다."""

        result = await self._require_compiled().ainvoke(
            self._build_input(session_id, user_message, history),
            config=self._merge_config(session_id, config),
        )
        content = self._extract_assistant_message(result)
        if content:
            return content
        detail = ExceptionDetail(
            code="CHAT_STREAM_EMPTY",
            cause="BaseChatGraph.ainvoke produced empty assistant_message",
        )
        raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)

    def stream_events(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """그래프 스트리밍 이벤트(custom/updates)를 표준 이벤트로 반환한다."""

        stream_config = self._merge_config(session_id, config)
        for mode, payload in self._require_compiled().stream(
            self._build_input(session_id, user_message, history),
            config=stream_config,
            stream_mode=["custom", "updates"],
        ):
            for event in self._to_events(mode=mode, payload=payload):
                node = str(event.get("node") or "").strip()
                event_name = str(event.get("event") or "").strip()
                if self._is_allowed_event(node=node, event_name=event_name):
                    yield event

    async def astream_events(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
        config: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """그래프 비동기 스트리밍 이벤트(custom/updates)를 표준 이벤트로 반환한다."""

        stream_config = self._merge_config(session_id, config)
        async for mode, payload in self._require_compiled().astream(
            self._build_input(session_id, user_message, history),
            config=stream_config,
            stream_mode=["custom", "updates"],
        ):
            for event in self._to_events(mode=mode, payload=payload):
                node = str(event.get("node") or "").strip()
                event_name = str(event.get("event") or "").strip()
                if self._is_allowed_event(node=node, event_name=event_name):
                    yield event

    def _require_compiled(self) -> Any:
        if self._compiled_graph is None:
            return self.compile()
        return self._compiled_graph

    def _merge_config(
        self,
        session_id: str,
        config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        if config:
            merged.update(config)
        configurable = merged.get("configurable")
        if not isinstance(configurable, dict):
            configurable = {}
        if not configurable.get("thread_id"):
            configurable["thread_id"] = session_id
        merged["configurable"] = configurable
        return merged

    def _to_events(self, mode: str, payload: Any) -> Iterator[dict[str, Any]]:
        if mode == "custom":
            if not isinstance(payload, dict):
                return
            node = str(payload.get("node") or "").strip()
            event = str(payload.get("event") or "").strip()
            if not node or not event:
                return
            yield {"node": node, "event": event, "data": payload.get("data")}
            return
        if mode != "updates":
            return
        if not isinstance(payload, dict):
            return
        for node_name, delta in payload.items():
            if not isinstance(delta, dict):
                continue
            for event_name, value in delta.items():
                yield {
                    "node": str(node_name),
                    "event": str(event_name),
                    "data": value,
                }

    def _extract_assistant_message(self, result: object) -> str:
        if isinstance(result, dict):
            raw = result.get("assistant_message")
            if isinstance(raw, str):
                if raw.strip():
                    return raw
        return ""

    def _build_input(
        self,
        session_id: str,
        user_message: str,
        history: list[Any],
    ) -> dict[str, Any]:
        payload = self._input_model(
            session_id=session_id,
            user_message=user_message,
            history=history,
            assistant_message="",
        )
        return payload.model_dump()

    def _normalize_stream_node(self, raw: StreamNodeConfig) -> dict[str, set[str]]:
        normalized: dict[str, set[str]] = {}
        for node, events in raw.items():
            node_name = str(node).strip()
            if not node_name:
                continue
            if isinstance(events, str):
                values = {events.strip()} if events.strip() else set()
                normalized[node_name] = values
                continue
            if not isinstance(events, Sequence):
                detail = ExceptionDetail(
                    code="CHAT_STREAM_NODE_INVALID",
                    cause=f"node={node_name}, value_type={type(events).__name__}",
                )
                raise BaseAppException("stream_node 설정 형식이 올바르지 않습니다.", detail)
            values = {str(item).strip() for item in events if str(item).strip()}
            normalized[node_name] = values
        return normalized

    def _is_allowed_event(self, node: str, event_name: str) -> bool:
        allowed = self._stream_node.get(node)
        if not allowed:
            return False
        return event_name in allowed
