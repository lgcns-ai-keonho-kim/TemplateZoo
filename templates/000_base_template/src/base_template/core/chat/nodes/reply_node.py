"""
목적: Chat 응답 생성 노드를 제공한다.
설명: 대화 이력을 LangChain 메시지로 변환해 LLM 스트리밍으로 답변을 생성한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/integrations/llm/client.py, src/base_template/core/chat/state/graph_state.py
"""

from __future__ import annotations

import os
from typing import Iterator, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate

from base_template.core.chat.models import ChatMessage, ChatRole
from base_template.core.chat.prompts import SYSTEM_PROMPT
from base_template.core.chat.state import ChatGraphState
from base_template.integrations.llm import LLMClient
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger


class ChatReplyNode:
    """LangGraph에서 사용하는 응답 생성 노드."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        logger: Optional[Logger] = None,
        system_prompt_template: PromptTemplate = SYSTEM_PROMPT,
    ) -> None:
        self._logger = logger or create_default_logger("ChatReplyNode")
        self._system_prompt_template = system_prompt_template
        self._llm_client = llm_client

    def run(self, state: ChatGraphState) -> dict[str, str]:
        """그래프 상태를 받아 어시스턴트 답변을 생성한다."""

        self._logger.info("Chat Reply 노드 실행")
        chunks = [chunk for chunk in self.stream(state) if chunk]
        content = "".join(chunks).strip()
        if not content:
            detail = ExceptionDetail(
                code="CHAT_STREAM_EMPTY",
                cause="reply node stream produced empty content",
            )
            raise BaseAppException("스트리밍 응답이 비어 있습니다.", detail)
        return {"assistant_message": content}

    def stream(self, state: ChatGraphState) -> Iterator[str]:
        """그래프 상태를 받아 어시스턴트 응답을 토큰 단위로 생성한다."""

        messages = self._build_messages(state)
        llm_client = self._get_llm_client()
        self._logger.info("Chat Reply 노드 스트리밍 실행")
        for chunk in llm_client.stream(messages):
            text = self._extract_text(chunk)
            if text:
                yield text

    def _get_llm_client(self) -> LLMClient:
        """LLM 클라이언트를 지연 초기화해 반환한다."""

        if self._llm_client is None:
            self._llm_client = self._build_default_llm_client()
        return self._llm_client

    def _build_default_llm_client(self) -> LLMClient:
        model = self._build_env_model()
        return LLMClient(
            model=model,
            name="chat-core-llm",
            logger=self._logger,
            log_payload=False,
            log_response=False,
        )

    def _build_env_model(self) -> BaseChatModel:
        provider = os.getenv("CHAT_LLM_PROVIDER", "gemini").strip().lower() or "gemini"
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                detail = ExceptionDetail(
                    code="CHAT_LLM_CONFIG_ERROR",
                    cause="OPENAI_API_KEY is missing",
                )
                raise BaseAppException("OPENAI_API_KEY 환경 변수가 필요합니다.", detail)
            try:
                from langchain_openai import ChatOpenAI
            except ImportError as error:
                detail = ExceptionDetail(
                    code="CHAT_LLM_DEPENDENCY_ERROR",
                    cause="langchain_openai is not installed",
                )
                raise BaseAppException(
                    "langchain_openai 의존성이 필요합니다.",
                    detail,
                    error,
                ) from error
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.2)

        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                detail = ExceptionDetail(
                    code="CHAT_LLM_CONFIG_ERROR",
                    cause="GEMINI_API_KEY or GOOGLE_API_KEY is missing",
                )
                raise BaseAppException(
                    "GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수가 필요합니다.",
                    detail,
                )
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError as error:
                detail = ExceptionDetail(
                    code="CHAT_LLM_DEPENDENCY_ERROR",
                    cause="langchain_google_genai is not installed",
                )
                raise BaseAppException(
                    "langchain_google_genai 의존성이 필요합니다.",
                    detail,
                    error,
                ) from error
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.2,
            )

        detail = ExceptionDetail(
            code="CHAT_LLM_PROVIDER_INVALID",
            cause=f"provider={provider}",
        )
        raise BaseAppException(
            "지원하지 않는 CHAT_LLM_PROVIDER 값입니다. gemini 또는 openai를 사용하세요.",
            detail,
        )

    def _history_to_langchain(self, history: list[ChatMessage]) -> list[BaseMessage]:
        lc_messages: list[BaseMessage] = []
        for message in history:
            if message.role == ChatRole.USER:
                lc_messages.append(HumanMessage(content=message.content))
            elif message.role == ChatRole.ASSISTANT:
                lc_messages.append(AIMessage(content=message.content))
            else:
                lc_messages.append(SystemMessage(content=message.content))
        return lc_messages

    def _build_messages(self, state: ChatGraphState) -> list[BaseMessage]:
        messages = [SystemMessage(content=self._system_prompt_template.format())]
        messages.extend(self._history_to_langchain(state.get("history", [])))
        messages.append(HumanMessage(content=state["user_message"]))
        return messages

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
            chunks = []
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
