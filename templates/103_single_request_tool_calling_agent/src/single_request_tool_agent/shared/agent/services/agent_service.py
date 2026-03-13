"""
목적: 1회성 Agent 실행 서비스를 제공한다.
설명: 그래프 스트림 이벤트를 직접 소비해 최종 응답과 Tool 추적 결과를 단건으로 집계한다.
디자인 패턴: 서비스 레이어
참조: src/single_request_tool_agent/core/agent/graphs/chat_graph.py
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from typing import Any
from uuid import uuid4

from single_request_tool_agent.core.agent.models import (
    AgentExecutionStatus,
    AgentRunResult,
    AgentToolTrace,
)
from single_request_tool_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)
from single_request_tool_agent.shared.logging import Logger, create_default_logger


class AgentService:
    """1회성 Agent 실행 서비스."""

    def __init__(
        self,
        *,
        graph: Any,
        timeout_seconds: float = 180.0,
        logger: Logger | None = None,
    ) -> None:
        self._graph = graph
        self._timeout_seconds = max(1.0, float(timeout_seconds))
        self._logger = logger or create_default_logger("AgentService")

    async def arun_once(self, request: str) -> AgentRunResult:
        """사용자 요청 1건을 실행해 단일 결과를 반환한다."""

        user_request = str(request or "").strip()
        if not user_request:
            detail = ExceptionDetail(code="AGENT_REQUEST_EMPTY", cause="request is empty")
            raise BaseAppException("요청 본문은 비어 있을 수 없습니다.", detail)

        run_id = str(uuid4())
        try:
            return await asyncio.wait_for(
                self._consume_graph(run_id=run_id, request=user_request),
                timeout=self._timeout_seconds,
            )
        except TimeoutError as error:
            detail = ExceptionDetail(
                code="AGENT_REQUEST_TIMEOUT",
                cause=f"run_id={run_id}, timeout_seconds={self._timeout_seconds}",
            )
            raise BaseAppException("Agent 요청 처리 시간이 초과되었습니다.", detail, error) from error

    def run_once(self, request: str) -> AgentRunResult:
        """동기 환경에서 사용자 요청 1건을 실행한다."""

        return asyncio.run(self.arun_once(request))

    async def _consume_graph(self, *, run_id: str, request: str) -> AgentRunResult:
        token_chunks: list[str] = []
        fallback_content = ""
        done_node = "response"
        tool_results: list[AgentToolTrace] = []

        async for event in self._iter_graph_events(run_id=run_id, request=request):
            node = str(event.get("node") or "").strip()
            event_name = str(event.get("event") or "").strip()
            data = event.get("data")

            if event_name == "token":
                text = str(data or "")
                if text:
                    token_chunks.append(text)
                    done_node = node or done_node
                continue

            if event_name == "assistant_message":
                candidate = str(data or "")
                if candidate.strip():
                    fallback_content = candidate
                    done_node = node or done_node
                continue

            if event_name in {"tool_result", "tool_error"} and isinstance(data, Mapping):
                tool_results.append(self._to_tool_trace(event_name=event_name, payload=data))
                continue

        output_text = "".join(token_chunks).strip()
        if not output_text:
            output_text = fallback_content.strip()
        if not output_text:
            detail = ExceptionDetail(
                code="AGENT_STREAM_EMPTY",
                cause=f"run_id={run_id}, graph returned empty content",
            )
            raise BaseAppException("Agent 응답이 비어 있습니다.", detail)

        status = (
            AgentExecutionStatus.BLOCKED
            if done_node == "blocked"
            else AgentExecutionStatus.COMPLETED
        )
        self._logger.info(f"agent.run.completed: run_id={run_id}, status={status.value}")
        return AgentRunResult(
            run_id=run_id,
            status=status,
            output_text=output_text,
            tool_results=tool_results,
        )

    async def _iter_graph_events(
        self,
        *,
        run_id: str,
        request: str,
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self._graph.astream_events(
            session_id=run_id,
            user_message=request,
            history=[],
            config={"configurable": {"thread_id": run_id}},
        ):
            yield event

    def _to_tool_trace(
        self,
        *,
        event_name: str,
        payload: Mapping[str, Any],
    ) -> AgentToolTrace:
        return AgentToolTrace(
            tool_name=str(payload.get("tool_name") or ""),
            status="SUCCESS" if event_name == "tool_result" else "FAILED",
            output=dict(payload.get("output") or {}),
            error_message=(
                None if event_name == "tool_result" else str(payload.get("error") or "")
            )
            or None,
            attempt=int(payload.get("attempt") or 1),
        )
