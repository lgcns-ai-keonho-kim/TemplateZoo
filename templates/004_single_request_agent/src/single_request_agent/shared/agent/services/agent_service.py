"""
목적: 1회성 Agent 실행 서비스를 제공한다.
설명: 그래프 스트림 이벤트를 직접 소비해 최종 응답을 단건으로 집계한다.
디자인 패턴: 서비스 레이어
참조: src/single_request_agent/core/agent/graphs/agent_graph.py
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from single_request_agent.core.agent.models import (
    AgentExecutionStatus,
    AgentRunResult,
)
from single_request_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)
from single_request_agent.shared.logging import Logger, create_default_logger


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

        async for event in self._iter_graph_events(run_id=run_id, request=request):
            event_name = str(event.get("event") or "").strip()
            data = event.get("data")

            if event_name == "token":
                text = str(data or "")
                if text:
                    token_chunks.append(text)
                continue

            if event_name == "assistant_message":
                candidate = str(data or "")
                if candidate.strip():
                    fallback_content = candidate
                continue

        output_text = "".join(token_chunks).strip()
        if not output_text:
            output_text = fallback_content.strip()
        if not output_text:
            detail = ExceptionDetail(
                code="AGENT_RESPONSE_EMPTY",
                cause=f"run_id={run_id}, graph returned empty content",
            )
            raise BaseAppException("Agent 응답이 비어 있습니다.", detail)

        status = AgentExecutionStatus.COMPLETED
        self._logger.info(f"agent.run.completed: run_id={run_id}, status={status.value}")
        return AgentRunResult(
            run_id=run_id,
            status=status,
            output_text=output_text,
        )

    async def _iter_graph_events(
        self,
        *,
        run_id: str,
        request: str,
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in self._graph.astream_events(
            run_id=run_id,
            user_message=request,
            history=[],
            config={"configurable": {"thread_id": run_id}},
        ):
            yield event
