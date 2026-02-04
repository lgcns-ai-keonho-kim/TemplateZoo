"""
목적: LangChain 기반 LLM 클라이언트를 제공한다.
설명: 오류 처리와 로깅 주입을 포함한 공통 인터페이스를 제공한다.
디자인 패턴: 어댑터 패턴
참조: src/base_template/shared/exceptions, src/base_template/shared/logging
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ...shared.exceptions import BaseAppException, ExceptionDetail
from ...shared.logging import Logger, create_default_logger


class LLMClient:
    """LangChain 기반 LLM 클라이언트 래퍼."""

    def __init__(
        self,
        client: Any,
        name: str = "llm-client",
        logger: Optional[Logger] = None,
    ) -> None:
        self._client = client
        self._name = name
        self._logger = logger or create_default_logger(self._name)

    def invoke(self, prompt: str, **kwargs) -> Any:
        """단일 프롬프트 호출을 수행한다."""

        self._logger.info("LLM 호출을 시작합니다.")
        try:
            if hasattr(self._client, "invoke"):
                return self._client.invoke(prompt, **kwargs)
            return self._client(prompt, **kwargs)
        except Exception as error:  # noqa: BLE001 - 외부 라이브러리 오류 캡처
            self._logger.error(f"LLM 호출 실패: {error}")
            detail = ExceptionDetail(code="LLM_INVOKE_ERROR", cause=str(error))
            raise BaseAppException("LLM 호출에 실패했습니다.", detail, error) from error

    def chat(self, messages: Iterable[Any], **kwargs) -> Any:
        """메시지 기반 대화 호출을 수행한다."""

        self._logger.info("LLM 대화 호출을 시작합니다.")
        try:
            if hasattr(self._client, "invoke"):
                return self._client.invoke(list(messages), **kwargs)
            return self._client(list(messages), **kwargs)
        except Exception as error:  # noqa: BLE001 - 외부 라이브러리 오류 캡처
            self._logger.error(f"LLM 대화 호출 실패: {error}")
            detail = ExceptionDetail(code="LLM_CHAT_ERROR", cause=str(error))
            raise BaseAppException("LLM 대화 호출에 실패했습니다.", detail, error) from error
