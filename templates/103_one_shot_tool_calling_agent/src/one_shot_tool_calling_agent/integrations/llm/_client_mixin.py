"""
목적: LLMClient 보조 메서드 믹스인을 제공한다.
설명: 로깅 보호, 백그라운드 실행, 메시지/결과 직렬화 및 청크 정규화를 분리한다.
디자인 패턴: 믹스인
참조: src/one_shot_tool_calling_agent/integrations/llm/client.py
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    BaseMessageChunk,
)
from langchain_core.outputs import ChatGenerationChunk, ChatResult

from one_shot_tool_calling_agent.shared.logging import LogContext, LogLevel


class _LLMClientMixin:
    """LLMClient의 보조 메서드를 제공한다."""

    _background_runner: Callable[..., None] | None
    _logger: Any
    _context_provider: Callable[[], Optional[LogContext]] | None

    def _run_background(self, fn: Callable[..., None], *args: Any) -> None:
        if self._background_runner is not None:
            try:
                self._background_runner(fn, *args)
            except Exception:  # noqa: BLE001 - 백그라운드 실패가 본 호출을 깨지 않도록 보호
                return
            return
        try:
            thread = threading.Thread(target=fn, args=args, daemon=True)
            thread.start()
        except Exception:  # noqa: BLE001 - 스레드 시작 실패가 본 호출을 깨지 않도록 보호
            return

    def _safe_log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext],
        metadata: Optional[dict],
    ) -> None:
        """로깅 실패가 본 호출을 깨지 않도록 보호한다."""

        try:
            self._logger.log(level, message, context=context, metadata=metadata)
        except Exception:  # noqa: BLE001 - 로깅은 best-effort로 동작해야 한다.
            return

    def _get_context(self) -> Optional[LogContext]:
        if not self._context_provider:
            return None
        try:
            return self._context_provider()
        except Exception:  # noqa: BLE001 - 로깅 실패 방지
            return None

    def _extract_usage_metadata(self, result: Optional[ChatResult]) -> Optional[dict]:
        if result is None:
            return None
        llm_output = getattr(result, "llm_output", None)
        if isinstance(llm_output, dict):
            usage = llm_output.get("usage_metadata")
            if isinstance(usage, dict):
                return usage
        generations = getattr(result, "generations", [])
        for item in generations:
            if isinstance(item, list):
                candidates = item
            else:
                candidates = [item]
            for generation in candidates:
                message = getattr(generation, "message", None)
                usage = getattr(message, "usage_metadata", None)
                if isinstance(usage, dict):
                    return usage
                response_metadata = getattr(message, "response_metadata", None)
                if isinstance(response_metadata, dict):
                    usage = response_metadata.get("usage_metadata")
                    if isinstance(usage, dict):
                        return usage
        return None

    def _serialize_message(self, message: BaseMessage) -> dict:
        if hasattr(message, "model_dump"):
            return message.model_dump(mode="json")
        if hasattr(message, "dict"):
            return message.dict()
        return {"text": str(message)}

    def _serialize_result(self, result: ChatResult) -> dict:
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json")
        if hasattr(result, "dict"):
            return result.dict()
        return {"text": str(result)}

    def _to_generation_chunk(self, chunk: Any) -> ChatGenerationChunk:
        """스트리밍 출력 객체를 ChatGenerationChunk로 정규화한다."""

        if isinstance(chunk, ChatGenerationChunk):
            return chunk
        return ChatGenerationChunk(message=self._to_message_chunk(chunk))

    def _to_message_chunk(self, chunk: Any) -> BaseMessageChunk:
        """스트리밍 출력 객체를 BaseMessageChunk로 정규화한다."""

        if isinstance(chunk, BaseMessageChunk):
            return chunk
        if isinstance(chunk, AIMessage):
            return AIMessageChunk(
                content=chunk.content,
                additional_kwargs=chunk.additional_kwargs,
                response_metadata=chunk.response_metadata,
                name=chunk.name,
                id=chunk.id,
                tool_calls=chunk.tool_calls,
                invalid_tool_calls=chunk.invalid_tool_calls,
                usage_metadata=chunk.usage_metadata,
            )
        if isinstance(chunk, BaseMessage):
            return AIMessageChunk(
                content=chunk.content,
                additional_kwargs=getattr(chunk, "additional_kwargs", {}),
                response_metadata=getattr(chunk, "response_metadata", {}),
                name=getattr(chunk, "name", None),
                id=getattr(chunk, "id", None),
            )
        return AIMessageChunk(content=str(chunk))

    def _to_text(self, content: Any) -> str:
        """메시지 콘텐츠를 문자열로 정규화한다."""

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if text is not None:
                        chunks.append(str(text))
                else:
                    chunks.append(str(item))
            return "".join(chunks)
        return str(content)
