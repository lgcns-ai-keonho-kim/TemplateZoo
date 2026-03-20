"""
목적: ToolExecNode 보조 메서드 믹스인을 제공한다.
설명: 스트림 이벤트 전송, 재시도 백오프, 예외 종료 흐름 보조를 분리한다.
디자인 패턴: 믹스인
참조: src/one_shot_tool_calling_agent/shared/agent/nodes/tool_exec_node.py
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from langgraph.config import get_stream_writer

from one_shot_tool_calling_agent.shared.agent.tools import ToolCall


class _ToolExecSupportMixin:
    """ToolExecNode 보조 메서드를 제공한다."""

    _node_name: str
    _logger: Any
    _success_key: str
    _failure_key: str

    def _build_failure_envelope(
        self,
        *,
        tool_call: ToolCall,
        error_message: str,
        error_code: str,
        attempt: int,
        duration_ms: int,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def _emit_tool_start(
        self,
        *,
        writer: Any | None,
        tool_call_id: str,
        tool_name: str,
        retry_for: str | None,
        attempt: int,
    ) -> None:
        if writer is None:
            return
        writer(
            {
                "node": self._node_name,
                "event": "tool_start",
                "data": {
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "retry_for": retry_for,
                    "attempt": attempt,
                },
            }
        )

    def _emit_tool_result(
        self, *, writer: Any | None, envelope: dict[str, Any]
    ) -> None:
        if writer is None:
            return
        writer(
            {
                "node": self._node_name,
                "event": "tool_result",
                "data": envelope,
            }
        )

    def _emit_tool_error(self, *, writer: Any | None, envelope: dict[str, Any]) -> None:
        if writer is None:
            return
        writer(
            {
                "node": self._node_name,
                "event": "tool_error",
                "data": envelope,
            }
        )

    def _sleep_backoff(self, *, backoffs: tuple[float, ...], attempt: int) -> None:
        delay = self._resolve_backoff_delay(backoffs=backoffs, attempt=attempt)
        if delay <= 0:
            return
        time.sleep(delay)

    async def _sleep_backoff_async(
        self, *, backoffs: tuple[float, ...], attempt: int
    ) -> None:
        delay = self._resolve_backoff_delay(backoffs=backoffs, attempt=attempt)
        if delay <= 0:
            return
        await asyncio.sleep(delay)

    def _resolve_backoff_delay(
        self, *, backoffs: tuple[float, ...], attempt: int
    ) -> float:
        if not backoffs:
            return 0.0
        index = max(0, min(attempt - 1, len(backoffs) - 1))
        return max(float(backoffs[index]), 0.0)

    def _build_unexpected_flow_result(
        self,
        *,
        tool_call: ToolCall,
        attempt: int,
        writer: Any | None,
    ) -> dict[str, Any]:
        """정상 분기에서 처리되지 않은 실행 흐름을 실패 결과로 강제 변환한다."""

        failure = self._build_failure_envelope(
            tool_call=tool_call,
            error_message="tool execution flow broken",
            error_code="TOOL_EXEC_FLOW_BROKEN",
            attempt=attempt,
            duration_ms=0,
        )
        self._logger.error(
            "tool execution reached unexpected terminal flow: "
            f"tool_name={failure.get('tool_name')}, tool_call_id={failure.get('tool_call_id')}"
        )
        self._emit_tool_error(writer=writer, envelope=failure)
        return {self._success_key: [], self._failure_key: [failure]}

    def _safe_get_stream_writer(self) -> Any | None:
        try:
            return get_stream_writer()
        except Exception:  # noqa: BLE001 - stream context 없는 실행을 허용한다.
            return None
