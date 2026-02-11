"""
목적: 상태 값 기반 메시지 선택 노드를 제공한다.
설명: 앞선 노드가 반환한 값을 읽어 Enum 메시지 집합에서 응답 메시지를 선택한다.
디자인 패턴: 전략 주입
참조: src/base_template/core/chat/nodes/safeguard_node.py
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any

from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger


class MessageNode:
    """
    상태 값 -> 메시지 Enum 매핑 노드.

    용도:
    - 앞선 분기/분류 노드 결과를 사용자 노출 문구로 변환한다.
    - 하드코딩 문자열 대신 Enum을 사용해 메시지 변경점을 한 곳에서 관리한다.
    """

    def __init__(
        self,
        *,
        messages: type[Enum],
        selector_key: str,
        output_key: str = "assistant_message",
        selector_to_member: Mapping[str, str] | None = None,
        default_member: str | None = None,
        logger: Logger | None = None,
    ) -> None:
        """
        Args:
            messages:
                메시지 소스 Enum 클래스.
                Enum 멤버의 `name` 또는 `value`를 기준으로 selector를 매칭한다.
                예) `SafeguardRejectionMessage`.

            selector_key:
                state에서 매핑 기준값을 읽어올 키.
                예) `"safeguard_result"`.

            output_key:
                선택된 메시지를 기록할 state 키.
                기본값 `"assistant_message"`.

            selector_to_member:
                selector 값 -> Enum 멤버명 매핑.
                예) `{"PROMPT_INJECTION": "PROMPT_INJETION"}`.
                LLM 출력 토큰과 Enum 키가 1:1이 아닐 때 사용한다.

            default_member:
                어떤 매핑에도 실패했을 때 사용할 Enum 멤버명.
                예) `"HARMFUL"`.

            logger:
                매핑 결과 로그 기록용 로거.
                `None`이면 `MessageNode` 기본 로거를 생성한다.
        """
        if not issubclass(messages, Enum):
            detail = ExceptionDetail(
                code="MESSAGE_NODE_CONFIG_INVALID",
                cause=f"messages={type(messages).__name__}",
            )
            raise BaseAppException("messages는 Enum 클래스여야 합니다.", detail)
        if not selector_key.strip():
            detail = ExceptionDetail(
                code="MESSAGE_NODE_CONFIG_INVALID",
                cause="selector_key is empty",
            )
            raise BaseAppException("selector_key는 비어 있을 수 없습니다.", detail)

        self._messages = messages
        self._selector_key = selector_key
        self._output_key = output_key
        self._default_member = default_member
        self._logger = logger or create_default_logger("MessageNode")
        self._selector_to_member = dict(selector_to_member or {})

    def run(self, state: Mapping[str, Any]) -> dict[str, str]:
        """
        state에서 selector를 읽어 메시지를 반환한다.

        매핑 우선순위:
        1) selector_to_member
        2) Enum member name 직접 매칭
        3) Enum member value 매칭
        4) default_member
        """
        raw_selector = state.get(self._selector_key)
        selector = str(raw_selector).strip() if raw_selector is not None else ""

        member = self._resolve_member(selector)
        if member is None:
            detail = ExceptionDetail(
                code="MESSAGE_NODE_MAPPING_NOT_FOUND",
                cause=f"selector_key={self._selector_key}, selector={selector!r}",
            )
            raise BaseAppException("메시지 매핑을 찾지 못했습니다.", detail)

        self._logger.debug(
            f"message node selected: selector={selector}, member={member.name}"
        )
        return {self._output_key: str(member.value)}

    def _resolve_member(self, selector: str) -> Enum | None:
        """selector를 Enum 멤버로 해석한다."""
        mapped = self._selector_to_member.get(selector)
        if mapped:
            member = self._member_by_name(mapped)
            if member is not None:
                return member

        member = self._member_by_name(selector)
        if member is not None:
            return member

        member = self._member_by_value(selector)
        if member is not None:
            return member

        if self._default_member:
            return self._member_by_name(self._default_member)
        return None

    def _member_by_name(self, name: str) -> Enum | None:
        target = name.strip()
        if not target:
            return None
        for member in self._messages:
            if member.name == target or member.name.lower() == target.lower():
                return member
        return None

    def _member_by_value(self, value: str) -> Enum | None:
        target = value.strip()
        if not target:
            return None
        for member in self._messages:
            if str(member.value).strip() == target:
                return member
        return None


__all__ = ["MessageNode"]
