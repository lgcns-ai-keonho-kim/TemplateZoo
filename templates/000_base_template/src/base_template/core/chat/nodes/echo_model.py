"""
목적: 기본 Chat 모델을 제공한다.
설명: 외부 LLM 키가 없는 환경에서도 동작 가능한 Echo 기반 모델을 구현한다.
디자인 패턴: 전략 패턴
참조: src/base_template/core/chat/nodes/reply_node.py
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ConfigDict, PrivateAttr

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import SimpleChatModel
from langchain_core.messages import BaseMessage, HumanMessage

from base_template.shared.logging import Logger, create_default_logger


class EchoChatModel(SimpleChatModel):
    """개발용 Echo Chat 모델."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _prefix: str = PrivateAttr(default="기본 응답")
    _logger: Logger = PrivateAttr()

    def __init__(self, prefix: str = "기본 응답", logger: Optional[Logger] = None) -> None:
        super().__init__()
        self._prefix = prefix
        self._logger = logger or create_default_logger("EchoChatModel")

    @property
    def _llm_type(self) -> str:
        return "echo"

    def _call(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> str:
        _ = stop
        _ = run_manager
        _ = kwargs
        user_text = self._extract_last_user_text(messages)
        self._logger.info("Echo 모델 응답 생성")
        if not user_text:
            return "입력된 사용자 메시지가 없습니다."
        return (
            f"{self._prefix}\n\n"
            f"질문: {user_text}\n"
            "답변: 현재는 기본 Echo 모델이 동작 중입니다. "
            "CHAT_LLM_PROVIDER 환경 변수를 설정하면 실제 LLM으로 확장할 수 있습니다."
        )

    def _extract_last_user_text(self, messages: list[BaseMessage]) -> str:
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                content = message.content
                if isinstance(content, str):
                    return content.strip()
                return str(content)
        return ""
