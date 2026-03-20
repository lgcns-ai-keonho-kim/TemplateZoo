"""
목적: Tool Registry 기반 범용 Tool 실행 노드를 제공한다.
설명: ToolCall을 읽어 등록된 함수를 실행하고 timeout/retry/이벤트 발행을 공통화한다.
디자인 패턴: 실행 오케스트레이터
참조: src/one_shot_tool_calling_agent/shared/agent/tools/registry.py, src/one_shot_tool_calling_agent/shared/agent/tools/types.py
"""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Optional

from langchain_core.runnables.config import RunnableConfig

from one_shot_tool_calling_agent.shared.agent.nodes._state_adapter import (
    coerce_state_mapping,
)
from one_shot_tool_calling_agent.shared.agent.nodes._tool_exec_support import (
    _ToolExecSupportMixin,
)
from one_shot_tool_calling_agent.shared.agent.tools import (
    ToolCall,
    ToolRegistry,
    ToolResult,
)
from one_shot_tool_calling_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)
from one_shot_tool_calling_agent.shared.logging import Logger, create_default_logger


class ToolExecNode(_ToolExecSupportMixin):
    """단건 Tool 실행을 담당하는 공용 노드."""

    def __init__(
        self,
        *,
        registry: ToolRegistry,
        node_name: str = "tool_exec",
        tool_call_key: str = "tool_call",
        success_key: str = "batch_tool_results",
        failure_key: str = "batch_tool_failures",
        logger: Logger | None = None,
    ) -> None:
        normalized_node_name = str(node_name or "").strip()
        if not normalized_node_name:
            detail = ExceptionDetail(
                code="TOOL_EXEC_NODE_CONFIG_INVALID",
                cause="node_name is empty",
            )
            raise BaseAppException("ToolExecNode 이름은 비어 있을 수 없습니다.", detail)

        if not isinstance(registry, ToolRegistry):
            detail = ExceptionDetail(
                code="TOOL_EXEC_NODE_CONFIG_INVALID",
                cause=f"registry_type={type(registry).__name__}",
            )
            raise BaseAppException(
                "ToolExecNode registry 설정이 올바르지 않습니다.", detail
            )

        self._registry = registry
        self._node_name = normalized_node_name
        self._tool_call_key = str(tool_call_key or "tool_call")
        self._success_key = str(success_key or "batch_tool_results")
        self._failure_key = str(failure_key or "batch_tool_failures")
        self._logger = logger or create_default_logger(
            f"ToolExecNode:{normalized_node_name}"
        )

    def run(
        self, state: object, config: Optional[RunnableConfig] = None
    ) -> dict[str, Any]:
        """LangGraph 동기 노드 진입점."""

        del config
        normalized_state = coerce_state_mapping(state)
        writer = self._safe_get_stream_writer()
        return self._run_sync(normalized_state, writer=writer)

    async def arun(
        self, state: object, config: Optional[RunnableConfig] = None
    ) -> dict[str, Any]:
        """LangGraph 비동기 노드 진입점."""

        del config
        normalized_state = coerce_state_mapping(state)
        writer = self._safe_get_stream_writer()
        return await self._run_async(normalized_state, writer=writer)

    def _run_sync(
        self, state: Mapping[str, Any], *, writer: Any | None
    ) -> dict[str, Any]:
        tool_call = self._extract_tool_call(state)
        tool_call_id = str(tool_call.get("tool_call_id") or "")
        tool_name = str(tool_call.get("tool_name") or "")
        retry_for = self._normalize_retry_for(tool_call.get("retry_for"))

        try:
            spec = self._registry.resolve(tool_name)
        except BaseAppException as error:
            failure = self._build_failure_envelope(
                tool_call=tool_call,
                error_message=error.message,
                error_code=error.detail.code,
                attempt=1,
                duration_ms=0,
            )
            self._emit_tool_error(writer=writer, envelope=failure)
            return {self._success_key: [], self._failure_key: [failure]}

        retry_count = max(0, int(spec.retry_count))
        attempt_limit = retry_count + 1
        backoffs = tuple(float(value) for value in spec.retry_backoff_seconds)

        for attempt in range(1, attempt_limit + 1):
            self._emit_tool_start(
                writer=writer,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                retry_for=retry_for,
                attempt=attempt,
            )
            started_at = time.monotonic()
            try:
                raw_result = self._invoke_sync_with_timeout(
                    fn=spec.fn,
                    tool_call=tool_call,
                    timeout_seconds=float(spec.timeout_seconds),
                )
                normalized = self._normalize_tool_result(raw_result)
                elapsed_ms = int((time.monotonic() - started_at) * 1000)
                if normalized["ok"] is True:
                    success = self._build_success_envelope(
                        tool_call=tool_call,
                        normalized=normalized,
                        attempt=attempt,
                        duration_ms=elapsed_ms,
                    )
                    self._emit_tool_result(writer=writer, envelope=success)
                    return {self._success_key: [success], self._failure_key: []}

                error_message = str(
                    normalized.get("error") or "Tool 실행에 실패했습니다."
                )
                if attempt < attempt_limit:
                    self._sleep_backoff(backoffs=backoffs, attempt=attempt)
                    continue

                failure = self._build_failure_envelope(
                    tool_call=tool_call,
                    error_message=error_message,
                    error_code="TOOL_RETRY_EXHAUSTED",
                    attempt=attempt,
                    duration_ms=elapsed_ms,
                )
                self._emit_tool_error(writer=writer, envelope=failure)
                return {self._success_key: [], self._failure_key: [failure]}
            except TimeoutError:
                elapsed_ms = int((time.monotonic() - started_at) * 1000)
                if attempt < attempt_limit:
                    self._sleep_backoff(backoffs=backoffs, attempt=attempt)
                    continue
                failure = self._build_failure_envelope(
                    tool_call=tool_call,
                    error_message=f"tool timeout exceeded ({spec.timeout_seconds}s)",
                    error_code="TOOL_TIMEOUT",
                    attempt=attempt,
                    duration_ms=elapsed_ms,
                )
                self._emit_tool_error(writer=writer, envelope=failure)
                return {self._success_key: [], self._failure_key: [failure]}
            except Exception as error:  # noqa: BLE001 - Tool 실행 오류를 실패 결과로 전환
                elapsed_ms = int((time.monotonic() - started_at) * 1000)
                if attempt < attempt_limit:
                    self._sleep_backoff(backoffs=backoffs, attempt=attempt)
                    continue
                failure = self._build_failure_envelope(
                    tool_call=tool_call,
                    error_message=str(error),
                    error_code="TOOL_RETRY_EXHAUSTED",
                    attempt=attempt,
                    duration_ms=elapsed_ms,
                )
                self._emit_tool_error(writer=writer, envelope=failure)
                return {self._success_key: [], self._failure_key: [failure]}

        return self._build_unexpected_flow_result(
            tool_call=tool_call,
            attempt=attempt_limit,
            writer=writer,
        )

    async def _run_async(
        self, state: Mapping[str, Any], *, writer: Any | None
    ) -> dict[str, Any]:
        tool_call = self._extract_tool_call(state)
        tool_call_id = str(tool_call.get("tool_call_id") or "")
        tool_name = str(tool_call.get("tool_name") or "")
        retry_for = self._normalize_retry_for(tool_call.get("retry_for"))

        try:
            spec = self._registry.resolve(tool_name)
        except BaseAppException as error:
            failure = self._build_failure_envelope(
                tool_call=tool_call,
                error_message=error.message,
                error_code=error.detail.code,
                attempt=1,
                duration_ms=0,
            )
            self._emit_tool_error(writer=writer, envelope=failure)
            return {self._success_key: [], self._failure_key: [failure]}

        retry_count = max(0, int(spec.retry_count))
        attempt_limit = retry_count + 1
        backoffs = tuple(float(value) for value in spec.retry_backoff_seconds)

        for attempt in range(1, attempt_limit + 1):
            self._emit_tool_start(
                writer=writer,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                retry_for=retry_for,
                attempt=attempt,
            )
            started_at = time.monotonic()
            try:
                raw_result = await self._invoke_async_with_timeout(
                    fn=spec.fn,
                    tool_call=tool_call,
                    timeout_seconds=float(spec.timeout_seconds),
                )
                normalized = self._normalize_tool_result(raw_result)
                elapsed_ms = int((time.monotonic() - started_at) * 1000)
                if normalized["ok"] is True:
                    success = self._build_success_envelope(
                        tool_call=tool_call,
                        normalized=normalized,
                        attempt=attempt,
                        duration_ms=elapsed_ms,
                    )
                    self._emit_tool_result(writer=writer, envelope=success)
                    return {self._success_key: [success], self._failure_key: []}

                error_message = str(
                    normalized.get("error") or "Tool 실행에 실패했습니다."
                )
                if attempt < attempt_limit:
                    await self._sleep_backoff_async(backoffs=backoffs, attempt=attempt)
                    continue

                failure = self._build_failure_envelope(
                    tool_call=tool_call,
                    error_message=error_message,
                    error_code="TOOL_RETRY_EXHAUSTED",
                    attempt=attempt,
                    duration_ms=elapsed_ms,
                )
                self._emit_tool_error(writer=writer, envelope=failure)
                return {self._success_key: [], self._failure_key: [failure]}
            except TimeoutError:
                elapsed_ms = int((time.monotonic() - started_at) * 1000)
                if attempt < attempt_limit:
                    await self._sleep_backoff_async(backoffs=backoffs, attempt=attempt)
                    continue
                failure = self._build_failure_envelope(
                    tool_call=tool_call,
                    error_message=f"tool timeout exceeded ({spec.timeout_seconds}s)",
                    error_code="TOOL_TIMEOUT",
                    attempt=attempt,
                    duration_ms=elapsed_ms,
                )
                self._emit_tool_error(writer=writer, envelope=failure)
                return {self._success_key: [], self._failure_key: [failure]}
            except Exception as error:  # noqa: BLE001 - Tool 실행 오류를 실패 결과로 전환
                elapsed_ms = int((time.monotonic() - started_at) * 1000)
                if attempt < attempt_limit:
                    await self._sleep_backoff_async(backoffs=backoffs, attempt=attempt)
                    continue
                failure = self._build_failure_envelope(
                    tool_call=tool_call,
                    error_message=str(error),
                    error_code="TOOL_RETRY_EXHAUSTED",
                    attempt=attempt,
                    duration_ms=elapsed_ms,
                )
                self._emit_tool_error(writer=writer, envelope=failure)
                return {self._success_key: [], self._failure_key: [failure]}

        return self._build_unexpected_flow_result(
            tool_call=tool_call,
            attempt=attempt_limit,
            writer=writer,
        )

    def _extract_tool_call(self, state: Mapping[str, Any]) -> ToolCall:
        raw_tool_call = state.get(self._tool_call_key)
        if not isinstance(raw_tool_call, Mapping):
            detail = ExceptionDetail(
                code="TOOL_EXEC_INPUT_INVALID",
                cause=f"{self._tool_call_key} is missing or not mapping",
            )
            raise BaseAppException("Tool 실행 입력이 올바르지 않습니다.", detail)

        tool_call_id = str(raw_tool_call.get("tool_call_id") or "").strip()
        if not tool_call_id:
            detail = ExceptionDetail(
                code="TOOL_EXEC_INPUT_INVALID",
                cause="tool_call_id is missing",
            )
            raise BaseAppException("Tool 호출 식별자가 누락되었습니다.", detail)

        tool_name = str(raw_tool_call.get("tool_name") or "").strip()
        if not tool_name:
            detail = ExceptionDetail(
                code="TOOL_EXEC_INPUT_INVALID",
                cause="tool_name is missing",
            )
            raise BaseAppException("Tool 이름이 누락되었습니다.", detail)

        args = raw_tool_call.get("args")
        tool_args = dict(args) if isinstance(args, Mapping) else {}
        return {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "args": tool_args,
            "session_id": str(raw_tool_call.get("session_id") or ""),
            "request_id": str(raw_tool_call.get("request_id") or ""),
            "retry_for": self._normalize_retry_for(raw_tool_call.get("retry_for")),
            "state": state,
        }

    def _invoke_sync_with_timeout(
        self, *, fn: Any, tool_call: ToolCall, timeout_seconds: float
    ) -> Any:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, tool_call)
            try:
                result = future.result(timeout=max(float(timeout_seconds), 0.001))
            except FutureTimeoutError as error:
                future.cancel()
                raise TimeoutError("tool sync execution timeout") from error

        if inspect.isawaitable(result):
            detail = ExceptionDetail(
                code="TOOL_EXEC_ASYNC_IN_SYNC_RUN",
                cause=f"tool={tool_call.get('tool_name')}",
            )
            raise BaseAppException(
                "비동기 Tool 함수는 arun 경로에서 실행해야 합니다.", detail
            )
        return result

    async def _invoke_async_with_timeout(
        self, *, fn: Any, tool_call: ToolCall, timeout_seconds: float
    ) -> Any:
        result = fn(tool_call)
        timeout_value = max(float(timeout_seconds), 0.001)
        if inspect.isawaitable(result):
            return await asyncio.wait_for(result, timeout=timeout_value)

        return await asyncio.wait_for(
            asyncio.to_thread(self._invoke_sync_result, fn, tool_call),
            timeout=timeout_value,
        )

    def _invoke_sync_result(self, fn: Any, tool_call: ToolCall) -> Any:
        result = fn(tool_call)
        if inspect.isawaitable(result):
            detail = ExceptionDetail(
                code="TOOL_EXEC_ASYNC_IN_SYNC_RUN",
                cause=f"tool={tool_call.get('tool_name')}",
            )
            raise BaseAppException(
                "비동기 Tool 함수는 arun 경로에서 실행해야 합니다.", detail
            )
        return result

    def _normalize_tool_result(self, raw_result: Any) -> ToolResult:
        if isinstance(raw_result, Mapping):
            result_map = {str(key): value for key, value in raw_result.items()}
            ok = bool(result_map.get("ok") is True)
            output_raw = result_map.get("output")
            output: dict[str, Any]
            if isinstance(output_raw, Mapping):
                output = {str(key): value for key, value in output_raw.items()}
            else:
                output = {}
            error_raw = result_map.get("error")
            error = None if error_raw in {None, ""} else str(error_raw)
            return {
                "ok": ok,
                "output": output,
                "error": error,
            }

        return {
            "ok": True,
            "output": {"value": raw_result},
            "error": None,
        }

    def _normalize_retry_for(self, raw_retry_for: object) -> str | None:
        candidate = str(raw_retry_for or "").strip()
        if not candidate:
            return None
        return candidate

    def _build_success_envelope(
        self,
        *,
        tool_call: ToolCall,
        normalized: ToolResult,
        attempt: int,
        duration_ms: int,
    ) -> dict[str, Any]:
        return {
            "tool_call_id": str(tool_call.get("tool_call_id") or ""),
            "retry_for": self._normalize_retry_for(tool_call.get("retry_for")),
            "tool_name": str(tool_call.get("tool_name") or ""),
            "ok": True,
            "output": dict(normalized.get("output") or {}),
            "error": None,
            "attempt": int(attempt),
            "duration_ms": int(duration_ms),
        }

    def _build_failure_envelope(
        self,
        *,
        tool_call: ToolCall,
        error_message: str,
        error_code: str,
        attempt: int,
        duration_ms: int,
    ) -> dict[str, Any]:
        return {
            "tool_call_id": str(tool_call.get("tool_call_id") or ""),
            "retry_for": self._normalize_retry_for(tool_call.get("retry_for")),
            "tool_name": str(tool_call.get("tool_name") or ""),
            "ok": False,
            "output": {},
            "error": str(error_message),
            "error_code": str(error_code),
            "attempt": int(attempt),
            "duration_ms": int(duration_ms),
        }


__all__ = ["ToolExecNode"]
