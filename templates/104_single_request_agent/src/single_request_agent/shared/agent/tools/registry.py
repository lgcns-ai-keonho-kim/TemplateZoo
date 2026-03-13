"""
목적: Tool Registry 구현체를 제공한다.
설명: ToolSpec 등록/조회/selector 주입 스펙 생성을 공통화한다.
디자인 패턴: 레지스트리
참조: src/single_request_agent/shared/agent/tools/types.py
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from single_request_agent.shared.agent.tools.types import (
    PlannerToolSpec,
    SelectorToolSpec,
    ToolFn,
    ToolSpec,
)
from single_request_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)


class ToolRegistry:
    """이름 기반 Tool 스펙 저장소."""

    def __init__(
        self,
        *,
        validate_module_prefix: bool = True,
        allowed_module_prefix: str = "single_request_agent.core.agent.tools",
    ) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._validate_module_prefix = bool(validate_module_prefix)
        self._allowed_module_prefix = str(allowed_module_prefix).strip()

    def add_tool(
        self,
        *,
        name: str,
        description: str,
        args_schema: dict[str, Any],
        fn: ToolFn,
        timeout_seconds: float = 30.0,
        retry_count: int = 2,
        retry_backoff_seconds: tuple[float, ...] = (0.5, 1.0),
        tags: Iterable[str] = (),
    ) -> None:
        """Tool을 등록한다."""

        normalized_name = str(name or "").strip()
        if not normalized_name:
            detail = ExceptionDetail(
                code="TOOL_REGISTRY_INVALID_NAME",
                cause="name is empty",
            )
            raise BaseAppException("Tool 이름이 올바르지 않습니다.", detail)

        if normalized_name in self._tools:
            detail = ExceptionDetail(
                code="TOOL_REGISTRY_DUPLICATE",
                cause=f"tool_name={normalized_name}",
            )
            raise BaseAppException("동일한 Tool 이름이 이미 등록되어 있습니다.", detail)

        self._validate_tool_module(fn=fn, name=normalized_name)
        try:
            spec = ToolSpec(
                name=normalized_name,
                description=str(description or "").strip(),
                args_schema=dict(args_schema),
                fn=fn,
                timeout_seconds=float(timeout_seconds),
                retry_count=int(retry_count),
                retry_backoff_seconds=tuple(
                    float(value) for value in retry_backoff_seconds
                ),
                tags=tuple(str(item).strip() for item in tags if str(item).strip()),
            )
        except ValueError as error:
            detail = ExceptionDetail(
                code="TOOL_REGISTRY_INVALID_SPEC",
                cause=f"tool_name={normalized_name}, error={error!s}",
            )
            raise BaseAppException(
                "Tool 등록 스펙이 올바르지 않습니다.", detail
            ) from error

        self._tools[normalized_name] = spec

    def register_spec(self, spec: ToolSpec) -> None:
        """사전 구성된 ToolSpec을 등록한다."""

        self.add_tool(
            name=spec.name,
            description=spec.description,
            args_schema=spec.args_schema,
            fn=spec.fn,
            timeout_seconds=spec.timeout_seconds,
            retry_count=spec.retry_count,
            retry_backoff_seconds=spec.retry_backoff_seconds,
            tags=spec.tags,
        )

    def resolve(self, name: str) -> ToolSpec:
        """이름으로 ToolSpec을 조회한다."""

        normalized_name = str(name or "").strip()
        spec = self._tools.get(normalized_name)
        if spec is not None:
            return spec
        detail = ExceptionDetail(
            code="TOOL_NOT_FOUND",
            cause=f"tool_name={normalized_name}",
        )
        raise BaseAppException("요청한 Tool을 찾을 수 없습니다.", detail)

    def has(self, name: str) -> bool:
        """등록 여부를 반환한다."""

        normalized_name = str(name or "").strip()
        return normalized_name in self._tools

    def get_tools(self) -> tuple[ToolSpec, ...]:
        """등록된 ToolSpec 스냅샷을 읽기 전용 튜플로 반환한다."""

        return tuple(self._tools.values())

    def list_specs(self) -> list[ToolSpec]:
        """등록된 ToolSpec 목록을 반환한다."""

        return list(self.get_tools())

    def list_for_selector(self) -> list[SelectorToolSpec]:
        """Tool selector 주입용 최소 스펙 목록을 반환한다."""

        return [spec.to_selector_spec() for spec in self.get_tools()]

    def list_for_planner(self) -> list[PlannerToolSpec]:
        """기존 planner 호환용 최소 스펙 목록을 반환한다."""

        return [spec.to_planner_spec() for spec in self.get_tools()]

    def _validate_tool_module(self, *, fn: ToolFn, name: str) -> None:
        if not self._validate_module_prefix:
            return
        if not self._allowed_module_prefix:
            return

        module_name = str(getattr(fn, "__module__", "") or "").strip()
        if module_name.startswith(self._allowed_module_prefix):
            return

        detail = ExceptionDetail(
            code="TOOL_REGISTRY_MODULE_INVALID",
            cause=(
                f"tool_name={name}, module={module_name}, "
                f"allowed_prefix={self._allowed_module_prefix}"
            ),
            hint="Tool 함수 구현은 core/agent/tools 하위에 위치해야 합니다.",
        )
        raise BaseAppException("Tool 함수 모듈 경로가 정책과 다릅니다.", detail)
