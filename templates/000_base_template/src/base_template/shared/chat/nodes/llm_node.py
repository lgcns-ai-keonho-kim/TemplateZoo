"""
목적: LLM 기반 범용 노드 구현체를 제공한다.
설명: LLM/프롬프트/노드 이름을 주입받아 LangGraph 노드 실행과 토큰 스트리밍을 공통화한다.
디자인 패턴: 전략 주입 + 템플릿 메서드
참조: src/base_template/core/chat/nodes/response_node.py
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langgraph.config import get_stream_writer

from base_template.core.chat.models import ChatMessage, ChatRole
from base_template.integrations.llm import LLMClient
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger


class LLMNode:
    """
    LLM 호출 기반 범용 노드.

    이 노드는 "상태(state) -> LLM 입력 메시지 변환 -> 스트리밍/최종 결과 반환" 흐름을 공통화한다.
    core 계층에서는 이 클래스를 상속하지 않고 모듈 조립(`node = LLMNode(...)`)으로 바로 쓰는 것을 권장한다.
    """

    def __init__(
        self,
        *,
        llm_client: LLMClient,
        node_name: str,
        system_prompt_template: PromptTemplate | None = None,
        output_key: str = "assistant_message",
        user_message_key: str = "user_message",
        history_key: str = "history",
        logger: Logger | None = None,
    ) -> None:
        """
        Args:
            llm_client:
                실제 모델 호출을 담당하는 클라이언트.
                `LLMClient`(invoke/ainvoke/stream/astream 지원) 주입을 전제로 한다.

            node_name:
                노드 식별 이름.
                - 스트리밍 이벤트의 `node` 필드로도 사용된다.
                - 공백 문자열은 허용하지 않는다.
                예) "reply", "safeguard", "summarize"

            system_prompt_template:
                시스템 프롬프트 템플릿.
                - `None`이면 시스템 메시지를 추가하지 않는다.
                - 값이 있으면 항상 첫 메시지(SystemMessage)로 삽입된다.

            output_key:
                노드 실행 결과를 state에 기록할 키 이름.
                기본값은 `"assistant_message"`이며,
                safeguard처럼 다른 결과를 내고 싶으면 `"safeguard_result"`처럼 변경한다.

            user_message_key:
                사용자 입력을 state에서 읽어올 키 이름.
                기본값 `"user_message"`.
                이 키가 없거나 비어 있으면 예외를 발생시킨다.

            history_key:
                이전 대화 이력을 state에서 읽어올 키 이름.
                기본값 `"history"`.
                - 해당 키가 없거나 list가 아니면 이력은 무시된다.
                - 이력을 의도적으로 끄고 싶으면 존재하지 않는 키 이름
                  (예: `"__skip_history__"`)을 넣어 사용한다.

            logger:
                노드 실행 로그 기록용 로거.
                `None`이면 `LLMNode:{node_name}` 이름의 기본 로거를 생성한다.
        """
        normalized_node_name = node_name.strip()
        if not normalized_node_name:
            detail = ExceptionDetail(code="CHAT_NODE_CONFIG_ERROR", cause="node_name is empty")
            raise BaseAppException("LLM 노드 이름은 비어 있을 수 없습니다.", detail)

        self._llm_client = llm_client
        self._node_name = normalized_node_name
        self._system_prompt_template = system_prompt_template
        self._output_key = output_key
        self._user_message_key = user_message_key
        self._history_key = history_key
        self._logger = logger or create_default_logger(f"LLMNode:{normalized_node_name}")

    def run(self, state: Mapping[str, Any]) -> dict[str, str]:
        """노드 상태를 받아 최종 답변 문자열을 생성한다."""

        self._logger.debug(f"{self._node_name} 노드 실행")
        chunks: list[str] = []
        writer = get_stream_writer()
        for chunk in self._iter_tokens(state, writer=writer):
            if chunk:
                chunks.append(chunk)
        return self._build_output(chunks)

    async def arun(self, state: Mapping[str, Any]) -> dict[str, str]:
        """노드 상태를 받아 비동기로 최종 답변 문자열을 생성한다."""

        self._logger.debug(f"{self._node_name} 노드 비동기 실행")
        chunks: list[str] = []
        writer = get_stream_writer()
        async for chunk in self._aiter_tokens(state, writer=writer):
            if chunk:
                chunks.append(chunk)
        return self._build_output(chunks)

    def stream(self, state: Mapping[str, Any]) -> Iterator[str]:
        """노드 상태를 받아 토큰 단위 응답을 생성한다."""

        yield from self._iter_tokens(state, writer=None)

    async def astream(self, state: Mapping[str, Any]) -> AsyncIterator[str]:
        """노드 상태를 받아 비동기 토큰 단위 응답을 생성한다."""

        async for chunk in self._aiter_tokens(state, writer=None):
            yield chunk

    def _iter_tokens(
        self,
        state: Mapping[str, Any],
        *,
        writer: Any | None = None,
    ) -> Iterator[str]:
        messages = self._build_messages(state)
        self._logger.debug(f"{self._node_name} 노드 스트리밍 실행")
        for chunk in self._llm_client.stream(messages):
            text = self._extract_text(chunk)
            if not text:
                continue
            if writer is not None:
                # LangGraph custom stream 이벤트 형식으로 토큰을 전달한다.
                # downstream(Service/Executor)에서 event="token" 기반으로 SSE 변환한다.
                writer({"node": self._node_name, "event": "token", "data": text})
            yield text

    async def _aiter_tokens(
        self,
        state: Mapping[str, Any],
        *,
        writer: Any | None = None,
    ) -> AsyncIterator[str]:
        messages = self._build_messages(state)
        self._logger.debug(f"{self._node_name} 노드 비동기 스트리밍 실행")
        async for chunk in self._llm_client.astream(messages):
            text = self._extract_text(chunk)
            if not text:
                continue
            if writer is not None:
                # 동기 버전과 동일한 이벤트 스키마를 유지한다.
                writer({"node": self._node_name, "event": "token", "data": text})
            yield text

    def _build_messages(self, state: Mapping[str, Any]) -> list[BaseMessage]:
        user_message = str(state.get(self._user_message_key, "") or "").strip()
        if not user_message:
            detail = ExceptionDetail(
                code="CHAT_NODE_INPUT_INVALID",
                cause=f"{self._user_message_key} is missing or empty",
            )
            raise BaseAppException("노드 입력 메시지가 비어 있습니다.", detail)

        messages: list[BaseMessage] = []
        if self._system_prompt_template is not None:
            messages.append(SystemMessage(content=self._system_prompt_template.format()))

        # NOTE:
        # history_key가 없거나 list가 아니면 이력은 자동으로 비활성화된다.
        # 즉, safeguard처럼 히스토리를 끄고 싶으면 history_key를 임의 문자열로 주입하면 된다.
        history = state.get(self._history_key, [])
        if isinstance(history, list):
            messages.extend(self._history_to_langchain(history))

        messages.append(HumanMessage(content=user_message))
        return messages

    def _history_to_langchain(self, history: list[Any]) -> list[BaseMessage]:
        lc_messages: list[BaseMessage] = []
        for item in history:
            role, content = self._resolve_role_and_content(item)
            if not content:
                continue
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(SystemMessage(content=content))
        return lc_messages

    def _resolve_role_and_content(self, item: Any) -> tuple[str, str]:
        if isinstance(item, ChatMessage):
            return item.role.value, item.content
        if isinstance(item, dict):
            role = str(item.get("role") or "system").strip().lower()
            content = str(item.get("content") or "")
            return role, content

        raw_role = getattr(item, "role", ChatRole.SYSTEM)
        if isinstance(raw_role, ChatRole):
            role = raw_role.value
        else:
            role = str(raw_role or "system").strip().lower()
        content = str(getattr(item, "content", "") or "")
        return role, content

    def _extract_text(self, message: object) -> str:
        content = self._resolve_content(message)
        return self._extract_content_text(content)

    def _resolve_content(self, message: object) -> object:
        if isinstance(message, BaseMessage):
            return message.content
        nested_message = getattr(message, "message", None)
        if isinstance(nested_message, BaseMessage):
            return nested_message.content
        if hasattr(message, "content"):
            return getattr(message, "content")
        return message

    def _extract_content_text(self, content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        chunks.append(str(text))
                else:
                    chunks.append(str(item))
            merged = "\n".join(chunks).strip()
            if merged:
                return merged
        return str(content)

    def _build_output(self, chunks: list[str]) -> dict[str, str]:
        content = "".join(chunks).strip()
        if not content:
            detail = ExceptionDetail(
                code="CHAT_STREAM_EMPTY",
                cause=f"{self._node_name} node stream produced empty content",
            )
            raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)
        return {self._output_key: content}


__all__ = ["LLMNode"]
