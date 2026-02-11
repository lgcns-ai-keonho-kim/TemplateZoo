"""
목적: ServiceExecutor의 queue-first 스트림 동작을 검증한다.
설명: start/token/done 순서, 서비스 예외 처리, done 누락 오류 처리를 확인한다.
디자인 패턴: 실행 코디네이터 단위 테스트
참조: src/base_template/shared/chat/services/service_executor.py
"""

from __future__ import annotations

import json

from base_template.shared.chat.services.service_executor import ServiceExecutor
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.runtime.queue import InMemoryQueue, QueueConfig


def _extract_payload(raw: str) -> dict:
    for line in str(raw).splitlines():
        if line.startswith("data: "):
            return json.loads(line[len("data: ") :].strip())
    raise AssertionError(f"SSE payload가 없습니다: {raw!r}")


class _SuccessService:
    def stream(self, session_id: str, user_query: str, context_window: int = 20):
        yield {"node": "reply", "event": "token", "data": "안녕"}
        yield {"node": "reply", "event": "token", "data": "하세요"}
        yield {"node": "reply", "event": "done", "data": "안녕하세요"}


class _ErrorService:
    def stream(self, session_id: str, user_query: str, context_window: int = 20):
        detail = ExceptionDetail(code="CHAT_STREAM_FAILED", cause="forced")
        raise BaseAppException("강제 실패", detail)
        yield  # pragma: no cover


class _NoDoneService:
    def stream(self, session_id: str, user_query: str, context_window: int = 20):
        yield {"node": "reply", "event": "token", "data": "중간 토큰"}


def test_service_executor_stream_success_order() -> None:
    """성공 스트림에서 start/token*/done 순서가 유지되는지 검증한다."""

    queue = InMemoryQueue(config=QueueConfig(default_timeout=0.05))
    executor = ServiceExecutor(service=_SuccessService(), queue=queue, timeout_seconds=3)

    payloads = [_extract_payload(item) for item in executor.run_stream("s-1", "hello", 20)]
    types = [item["type"] for item in payloads]

    assert types == ["start", "token", "token", "done"]
    assert payloads[-1]["status"] == "COMPLETED"
    assert payloads[-1]["content"] == ""


def test_service_executor_stream_service_error_emits_error() -> None:
    """서비스 예외 발생 시 error 이벤트가 송출되는지 검증한다."""

    queue = InMemoryQueue(config=QueueConfig(default_timeout=0.05))
    executor = ServiceExecutor(service=_ErrorService(), queue=queue, timeout_seconds=3)

    payloads = [_extract_payload(item) for item in executor.run_stream("s-2", "hello", 20)]

    assert payloads[0]["type"] == "start"
    assert payloads[-1]["type"] == "error"
    assert payloads[-1]["status"] == "FAILED"
    assert "강제 실패" in str(payloads[-1]["error_message"] or "")


def test_service_executor_stream_missing_done_emits_error() -> None:
    """done 이벤트 없이 종료되면 error 이벤트를 반환하는지 검증한다."""

    queue = InMemoryQueue(config=QueueConfig(default_timeout=0.05))
    executor = ServiceExecutor(service=_NoDoneService(), queue=queue, timeout_seconds=3)

    payloads = [_extract_payload(item) for item in executor.run_stream("s-3", "hello", 20)]

    assert payloads[0]["type"] == "start"
    assert payloads[1]["type"] == "token"
    assert payloads[-1]["type"] == "error"
    assert payloads[-1]["status"] == "FAILED"
