"""
목적: Chat 응답 생성 노드를 제공한다.
설명: 대화 이력을 LangChain 메시지로 변환해 LLM 호출 후 답변 문자열을 반환한다.
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
from base_template.core.chat.nodes.echo_model import EchoChatModel
from base_template.core.chat.prompts import SYSTEM_PROMPT
from base_template.core.chat.state import ChatGraphState
from base_template.integrations.llm import LLMClient
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
        self._llm_client = llm_client or self._build_default_llm_client()

    def run(self, state: ChatGraphState) -> dict[str, str]:
        """그래프 상태를 받아 어시스턴트 답변을 생성한다."""

        messages = self._build_messages(state)

        self._logger.info("Chat Reply 노드 실행")
        result = self._llm_client.invoke(messages)
        content = self._extract_text(result)
        return {"assistant_message": content}

    def stream(self, state: ChatGraphState) -> Iterator[str]:
        """그래프 상태를 받아 어시스턴트 응답을 토큰 단위로 생성한다."""

        messages = self._build_messages(state)
        self._logger.info("Chat Reply 노드 스트리밍 실행")
        for chunk in self._llm_client.stream(messages):
            text = self._extract_text(chunk)
            if text:
                yield text

    def _build_default_llm_client(self) -> LLMClient:
        model = self._build_env_model() or EchoChatModel(logger=self._logger)
        return LLMClient(
            model=model,
            name="chat-core-llm",
            logger=self._logger,
            log_payload=False,
            log_response=False,
        )

    def _build_env_model(self) -> Optional[BaseChatModel]:
        provider = os.getenv("CHAT_LLM_PROVIDER", "gemini").strip().lower()
        if provider in {"", "echo"}:
            return None
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self._logger.warning("OPENAI_API_KEY가 없어 Echo 모델로 대체합니다.")
                return None
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                self._logger.warning("langchain_openai 모듈이 없어 Echo 모델로 대체합니다.")
                return None
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            return ChatOpenAI(model=model_name, api_key=api_key, temperature=0.2)

        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                self._logger.warning("GEMINI_API_KEY가 없어 Echo 모델로 대체합니다.")
                return None
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                self._logger.warning(
                    "langchain_google_genai 모듈이 없어 Echo 모델로 대체합니다."
                )
                return None
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.2,
            )

        if provider:
            self._logger.warning("지원하지 않는 CHAT_LLM_PROVIDER입니다. Echo 모델을 사용합니다.")
        return None

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
