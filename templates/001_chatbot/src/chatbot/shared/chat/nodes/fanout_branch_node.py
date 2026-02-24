"""
목적: 리스트 기반 fan-out 분기 라우터 노드를 제공한다.
설명: state의 목록 입력을 검증해 Send 목록으로 변환하거나 기본 분기로 폴백한다.
디자인 패턴: 규칙 기반 라우터
참조: src/chatbot/core/chat/graphs/chat_graph.py, src/chatbot/shared/chat/nodes/_state_adapter.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from langchain_core.runnables.config import RunnableConfig

from chatbot.shared.chat.nodes._state_adapter import coerce_state_mapping
from chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from chatbot.shared.logging import Logger, create_default_logger

try:
    from langgraph.constants import Send
except ImportError:  # pragma: no cover - langgraph 버전별 import 경로 차이
    from langgraph.types import Send


class FanoutBranchNode:
    """state 목록 값을 fan-out Send 목록으로 변환하는 범용 라우터 노드."""

    def __init__(
        self,
        *,
        items_key: str,
        target_node: str,
        default_branch: str,
        logger: Logger | None = None,
    ) -> None:
        """
        Args:
            items_key:
                fan-out 대상으로 읽을 state 키.
                예) `"rag_relevance_judge_inputs"`.

            target_node:
                각 항목을 전달할 대상 노드 이름.
                예) `"rag_relevance_judge"`.

            default_branch:
                fan-out 입력이 비정상/비어있을 때 이동할 기본 분기 이름.
                예) `"rag_relevance_collect"`.

            logger:
                분기 결정 로그 기록용 로거.
                `None`이면 `FanoutBranchNode` 기본 로거를 생성한다.
        """
        normalized_items_key = items_key.strip()
        if not normalized_items_key:
            detail = ExceptionDetail(
                code="FANOUT_BRANCH_NODE_CONFIG_INVALID",
                cause="items_key is empty",
            )
            raise BaseAppException("items_key는 비어 있을 수 없습니다.", detail)

        normalized_target_node = target_node.strip()
        if not normalized_target_node:
            detail = ExceptionDetail(
                code="FANOUT_BRANCH_NODE_CONFIG_INVALID",
                cause="target_node is empty",
            )
            raise BaseAppException("target_node는 비어 있을 수 없습니다.", detail)

        normalized_default_branch = default_branch.strip()
        if not normalized_default_branch:
            detail = ExceptionDetail(
                code="FANOUT_BRANCH_NODE_CONFIG_INVALID",
                cause="default_branch is empty",
            )
            raise BaseAppException("default_branch는 비어 있을 수 없습니다.", detail)

        self._items_key = normalized_items_key
        self._target_node = normalized_target_node
        self._default_branch = normalized_default_branch
        self._logger = logger or create_default_logger("FanoutBranchNode")

    def route(
        self,
        state: object,
        config: Optional[RunnableConfig] = None,
    ) -> str | list[Send]:
        """
        LangGraph `add_conditional_edges`용 fan-out 라우팅 진입점.

        Args:
            state: LangGraph가 전달한 노드 상태 객체.
            config: Runnable 설정(사용하지 않음).

        Returns:
            유효 항목이 있으면 `Send` 목록, 없으면 `default_branch`.
        """
        del config
        return self._route(coerce_state_mapping(state))

    def run(
        self,
        state: object,
        config: Optional[RunnableConfig] = None,
    ) -> str | list[Send]:
        """
        `route()`와 동일한 fan-out 분기 진입점.

        Args:
            state: LangGraph가 전달한 노드 상태 객체.
            config: Runnable 설정(사용하지 않음).

        Returns:
            유효 항목이 있으면 `Send` 목록, 없으면 `default_branch`.
        """
        return self.route(state=state, config=config)

    def _route(self, state: Mapping[str, Any]) -> str | list[Send]:
        """state를 읽어 fan-out 분기 결과를 계산한다."""
        raw_items = state.get(self._items_key)
        if not isinstance(raw_items, list):
            self._logger.debug(
                "fanout branch selected default: items_key=%s cause=not_list"
                % self._items_key
            )
            return self._default_branch

        sends: list[Send] = []
        invalid_item_count = 0
        for item in raw_items:
            if not isinstance(item, Mapping):
                invalid_item_count += 1
                continue
            sends.append(Send(self._target_node, dict(item)))

        if not sends:
            self._logger.debug(
                "fanout branch selected default: items_key=%s total=%s invalid=%s cause=empty_send"
                % (self._items_key, len(raw_items), invalid_item_count)
            )
            return self._default_branch

        self._logger.debug(
            "fanout branch selected sends: items_key=%s total=%s invalid=%s sends=%s target=%s"
            % (
                self._items_key,
                len(raw_items),
                invalid_item_count,
                len(sends),
                self._target_node,
            )
        )
        return sends


__all__ = ["FanoutBranchNode"]
