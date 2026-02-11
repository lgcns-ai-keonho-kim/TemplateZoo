"""
목적: 상태 값 기반 분기 노드를 제공한다.
설명: 입력 상태값을 정규화해 브랜치 키를 계산하고 다음 conditional edge 선택값을 반환한다.
디자인 패턴: 규칙 기반 라우터
참조: src/base_template/core/chat/nodes/safeguard_route_node.py
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from base_template.shared.logging import Logger, create_default_logger


class BranchNode:
    """
    상태값을 기반으로 분기 키를 계산하는 범용 노드.

    용도:
    - LangGraph `add_conditional_edges`에서 사용할 분기 키를 state에 기록한다.
    - 라우팅 규칙(맵/별칭/허용값/폴백)을 선언적으로 조합해 재사용한다.
    """

    def __init__(
        self,
        *,
        selector_key: str,
        branch_map: Mapping[str, str],
        default_branch: str,
        output_key: str = "branch",
        aliases: Mapping[str, str] | None = None,
        normalize_case: bool = True,
        allowed_selectors: Collection[str] | None = None,
        fallback_selector: str | None = None,
        write_normalized_to: str | None = None,
        logger: Logger | None = None,
    ) -> None:
        """
        Args:
            selector_key:
                분기 기준이 되는 state 키.
                예) `"safeguard_result"`.

            branch_map:
                selector 값 -> branch 이름 매핑.
                예) `{"PASS": "reply"}`.
                매핑되지 않은 값은 `default_branch`를 사용한다.

            default_branch:
                branch_map에 없는 값일 때 사용할 기본 분기 이름.
                예) `"blocked"`.

            output_key:
                계산된 분기 이름을 state에 기록할 키.
                예) `"branch"`, `"safeguard_route"`.

            aliases:
                selector 별칭 정규화 맵.
                예) `{"PROMPT_INJECTION": "PROMPT_INJETION"}`.
                LLM 출력 표기가 일관되지 않을 때 표준 토큰으로 통일할 수 있다.

            normalize_case:
                selector/aliases/allowed_selectors/fallback_selector를 대문자 정규화할지 여부.
                기본값 `True`.

            allowed_selectors:
                허용할 selector 집합.
                값이 지정되면, 정규화 결과가 집합에 없을 때 `fallback_selector`를 적용한다.
                예) `{"PASS", "PII", "HARMFUL", "PROMPT_INJETION"}`.

            fallback_selector:
                허용 selector 검증 실패 시 강제로 치환할 selector.
                예) `"HARMFUL"`.

            write_normalized_to:
                정규화된 selector를 다시 state에 기록할 키.
                예) `"safeguard_result"`.
                원본 토큰을 표준 토큰으로 교정해 다음 노드(MessageNode 등)가 바로 쓰게 할 때 유용하다.

            logger:
                분기 결정 로그 기록용 로거.
                `None`이면 `BranchNode` 기본 로거를 생성한다.
        """
        self._selector_key = selector_key
        self._normalize_case = normalize_case
        self._branch_map = self._normalize_mapping(dict(branch_map))
        self._default_branch = default_branch
        self._output_key = output_key
        self._aliases = self._normalize_mapping(dict(aliases or {}))
        self._allowed_selectors = self._normalize_collection(allowed_selectors)
        self._fallback_selector = self._normalize_value(fallback_selector)
        self._write_normalized_to = write_normalized_to
        self._logger = logger or create_default_logger("BranchNode")

    def run(self, state: Mapping[str, Any]) -> dict[str, str]:
        """state를 읽어 branch 결과 payload를 반환한다."""
        raw_selector = state.get(self._selector_key)
        selector = str(raw_selector or "").strip()
        selector = self._normalize_value(selector)
        normalized = self._aliases.get(selector, selector)
        if self._allowed_selectors is not None and normalized not in self._allowed_selectors:
            if self._fallback_selector is not None:
                normalized = self._fallback_selector

        branch = self._branch_map.get(normalized, self._default_branch)
        payload = {self._output_key: branch}
        if self._write_normalized_to is not None:
            payload[self._write_normalized_to] = normalized

        self._logger.debug(
            f"branch node selected: selector={selector} normalized={normalized} branch={branch}"
        )
        return payload

    def _normalize_value(self, value: str | None) -> str:
        """입력 문자열을 trim 후 필요 시 대문자로 정규화한다."""
        normalized = str(value or "").strip()
        if self._normalize_case:
            return normalized.upper()
        return normalized

    def _normalize_mapping(self, mapping: Mapping[str, str]) -> dict[str, str]:
        """매핑의 key를 정규화해 내부 lookup 비용을 줄인다."""
        out: dict[str, str] = {}
        for key, value in mapping.items():
            out[self._normalize_value(str(key))] = str(value)
        return out

    def _normalize_collection(self, values: Collection[str] | None) -> set[str] | None:
        """허용 selector 집합을 정규화한다."""
        if values is None:
            return None
        return {self._normalize_value(str(item)) for item in values if str(item).strip()}


__all__ = ["BranchNode"]
