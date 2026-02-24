"""
목적: 범용 함수 실행 노드를 제공한다.
설명: state를 입력받아 주입된 함수를 실행하고 반환 Mapping을 LangGraph state 업데이트 payload로 반환한다.
디자인 패턴: 함수 주입(Function Injection)
참조: src/rag_chatbot/core/chat/nodes/rag_keyword_node.py, src/rag_chatbot/shared/chat/nodes/_state_adapter.py
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Optional

from langchain_core.runnables.config import RunnableConfig

from rag_chatbot.shared.chat.nodes._state_adapter import coerce_state_mapping
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.logging import Logger, create_default_logger


class FunctionNode:
    """주입된 함수를 실행하는 범용 노드."""

    def __init__(
        self,
        *,
        fn: Callable[[Mapping[str, Any]], Mapping[str, Any] | Awaitable[Mapping[str, Any]]],
        node_name: str,
        logger: Logger | None = None,
    ) -> None:
        if not callable(fn):
            detail = ExceptionDetail(
                code="FUNCTION_NODE_CONFIG_INVALID",
                cause="fn is not callable",
            )
            raise BaseAppException("FunctionNode 설정이 올바르지 않습니다.", detail)

        normalized_node_name = node_name.strip()
        if not normalized_node_name:
            detail = ExceptionDetail(
                code="FUNCTION_NODE_CONFIG_INVALID",
                cause="node_name is empty",
            )
            raise BaseAppException("FunctionNode 이름은 비어 있을 수 없습니다.", detail)

        self._fn = fn
        self._node_name = normalized_node_name
        self._logger = logger or create_default_logger(f"FunctionNode:{normalized_node_name}")

    def run(self, state: object, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
        """LangGraph 동기 노드 진입점."""

        del config
        normalized_state = coerce_state_mapping(state)
        self._logger.debug(f"{self._node_name} 노드 실행")
        try:
            result = self._fn(normalized_state)
            if inspect.isawaitable(result):
                detail = ExceptionDetail(
                    code="FUNCTION_NODE_ASYNC_IN_SYNC_RUN",
                    cause=f"{self._node_name}에서 awaitable이 반환되었습니다.",
                    hint="비동기 함수는 arun으로 실행해야 합니다.",
                )
                raise BaseAppException("비동기 함수는 arun으로 실행해야 합니다.", detail)
        except BaseAppException:
            raise
        except Exception as error:  # noqa: BLE001 - 외부 함수 오류를 도메인 예외로 래핑
            detail = ExceptionDetail(
                code="FUNCTION_NODE_EXECUTION_ERROR",
                cause=f"{self._node_name} 실행 중 오류가 발생했습니다.",
                metadata={"error": repr(error)},
            )
            raise BaseAppException("함수 노드 실행에 실패했습니다.", detail, error) from error

        if not isinstance(result, Mapping):
            detail = ExceptionDetail(
                code="FUNCTION_NODE_OUTPUT_INVALID",
                cause=f"output_type={type(result).__name__}",
            )
            raise BaseAppException("함수 노드 출력 형식이 올바르지 않습니다.", detail)

        return {str(key): value for key, value in result.items()}

    async def arun(self, state: object, config: Optional[RunnableConfig] = None) -> dict[str, Any]:
        """LangGraph 비동기 노드 진입점."""

        del config
        normalized_state = coerce_state_mapping(state)
        self._logger.debug(f"{self._node_name} 노드 비동기 실행")
        try:
            result = self._fn(normalized_state)
            if inspect.isawaitable(result):
                result = await result
        except BaseAppException:
            raise
        except Exception as error:  # noqa: BLE001 - 외부 함수 오류를 도메인 예외로 래핑
            detail = ExceptionDetail(
                code="FUNCTION_NODE_EXECUTION_ERROR",
                cause=f"{self._node_name} 실행 중 오류가 발생했습니다.",
                metadata={"error": repr(error)},
            )
            raise BaseAppException("함수 노드 실행에 실패했습니다.", detail, error) from error

        if not isinstance(result, Mapping):
            detail = ExceptionDetail(
                code="FUNCTION_NODE_OUTPUT_INVALID",
                cause=f"output_type={type(result).__name__}",
            )
            raise BaseAppException("함수 노드 출력 형식이 올바르지 않습니다.", detail)

        return {str(key): value for key, value in result.items()}


def function_node(
    *,
    fn: Callable[[Mapping[str, Any]], Mapping[str, Any] | Awaitable[Mapping[str, Any]]],
    node_name: str,
    logger: Logger | None = None,
) -> FunctionNode:
    """주입 함수 기반 노드를 생성한다."""

    return FunctionNode(fn=fn, node_name=node_name, logger=logger)


__all__ = ["FunctionNode", "function_node"]
