"""
목적: EmbeddingClient 보조 메서드 믹스인을 제공한다.
설명: 임베딩 호출 로깅/백그라운드 실행/컨텍스트 조회 책임을 분리한다.
디자인 패턴: 믹스인
참조: src/tool_proxy_agent/integrations/embedding/client.py
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from tool_proxy_agent.shared.logging import LogContext, LogLevel


class _EmbeddingClientMixin:
    """EmbeddingClient의 보조 메서드를 제공한다."""

    _background_runner: Callable[..., None] | None
    _logger: Any
    _context_provider: Callable[[], LogContext | None] | None

    def _base_metadata(self, action: str) -> dict[str, Any]:
        raise NotImplementedError

    def _log_start(
        self,
        *,
        action: str,
        input_count: int,
        input_chars: int,
        payload: Any | None,
    ) -> None:
        metadata = self._base_metadata(action)
        metadata.update(
            {"input_count": int(input_count), "input_chars": int(input_chars)}
        )
        if payload is not None:
            metadata["payload"] = payload
        self._safe_log(
            LogLevel.INFO,
            f"Embedding {action} 호출 시작",
            context=self._get_context(),
            metadata=metadata,
        )

    def _log_success(
        self,
        action: str,
        start: float,
        *,
        input_count: int,
        input_chars: int,
        output_count: int,
        dimension: int,
        response: Any | None,
    ) -> None:
        metadata = self._base_metadata(action)
        metadata.update(
            {
                "duration_ms": int((time.monotonic() - start) * 1000),
                "success": True,
                "input_count": int(input_count),
                "input_chars": int(input_chars),
                "output_count": int(output_count),
                "dimension": int(dimension),
            }
        )
        if response is not None:
            metadata["response"] = response
        self._safe_log(
            LogLevel.INFO,
            f"Embedding {action} 호출 성공",
            context=self._get_context(),
            metadata=metadata,
        )

    def _log_error(
        self,
        action: str,
        error: Exception,
        start: float,
        *,
        input_count: int,
        input_chars: int,
    ) -> None:
        metadata = self._base_metadata(action)
        metadata.update(
            {
                "duration_ms": int((time.monotonic() - start) * 1000),
                "success": False,
                "error_type": type(error).__name__,
                "input_count": int(input_count),
                "input_chars": int(input_chars),
            }
        )
        self._safe_log(
            LogLevel.ERROR,
            f"Embedding {action} 호출 실패: {error}",
            context=self._get_context(),
            metadata=metadata,
        )

    def _safe_log(
        self,
        level: LogLevel,
        message: str,
        *,
        context: LogContext | None,
        metadata: dict[str, Any] | None,
    ) -> None:
        def _emit() -> None:
            try:
                self._logger.log(level, message, context=context, metadata=metadata)
            except Exception:  # noqa: BLE001
                return

        self._run_background(_emit)

    def _run_background(self, fn: Callable[..., None], *args: Any) -> None:
        if self._background_runner is not None:
            try:
                self._background_runner(fn, *args)
            except Exception:  # noqa: BLE001
                return
            return
        try:
            thread = threading.Thread(target=fn, args=args, daemon=True)
            thread.start()
        except Exception:  # noqa: BLE001
            return

    def _get_context(self) -> LogContext | None:
        if self._context_provider is None:
            return None
        try:
            return self._context_provider()
        except Exception:  # noqa: BLE001
            return None
