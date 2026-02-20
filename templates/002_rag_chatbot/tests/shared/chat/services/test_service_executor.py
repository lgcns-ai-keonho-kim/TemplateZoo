"""
목적: ServiceExecutor의 JobQueue/EventBuffer 동작을 검증한다.
설명: submit_job 이후 stream_events에서 start/token/done 순서와 오류 처리를 확인한다.
디자인 패턴: 실행 코디네이터 단위 테스트
참조: src/rag_chatbot/shared/chat/services/service_executor.py
"""

from __future__ import annotations
import time
import json
from dataclasses import dataclass

from rag_chatbot.shared.chat.services.service_executor import ServiceExecutor
from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from rag_chatbot.shared.runtime.buffer import EventBufferConfig, InMemoryEventBuffer
from rag_chatbot.shared.runtime.queue import InMemoryQueue, QueueConfig


def _extract_payload(raw: str) -> dict:
    for line in str(raw).splitlines():
        if line.startswith("data: "):
            return json.loads(line[len("data: ") :].strip())
    raise AssertionError(f"SSE payload가 없습니다: {raw!r}")


@dataclass
class _Session:
    session_id: str


class _BaseService:
    def create_session(self, session_id: str | None = None, title: str | None = None):
        return _Session(session_id=session_id or "generated-session")

    def get_session(self, session_id: str):
        return _Session(session_id=session_id)

    def persist_assistant_message(
        self,
        session_id: str,
        request_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> bool:
        del session_id, request_id, content, metadata
        return True


class _SuccessService(_BaseService):
    def stream(self, session_id: str, user_query: str, context_window: int = 20):
        yield {"node": "response", "event": "token", "data": "안녕"}
        yield {"node": "response", "event": "token", "data": "하세요"}
        yield {"node": "response", "event": "done", "data": "안녕하세요"}


class _ErrorService(_BaseService):
    def stream(self, session_id: str, user_query: str, context_window: int = 20):
        detail = ExceptionDetail(code="CHAT_STREAM_FAILED", cause="forced")
        raise BaseAppException("강제 실패", detail)
        yield  # pragma: no cover


class _NoDoneService(_BaseService):
    def stream(self, session_id: str, user_query: str, context_window: int = 20):
        yield {"node": "response", "event": "token", "data": "중간 토큰"}


class _ReferenceService(_BaseService):
    def stream(self, session_id: str, user_query: str, context_window: int = 20):
        yield {"node": "response", "event": "token", "data": "답변"}
        yield {
            "node": "rag",
            "event": "references",
            "data": [
                {
                    "type": "reference",
                    "content": "본문",
                    "metadata": {"index": 1, "file_name": "manual.pdf"},
                }
            ],
        }
        yield {
            "node": "response",
            "event": "done",
            "data": "답변",
        }


def test_service_executor_stream_success_order() -> None:
    """성공 스트림에서 start/token*/done 순서가 유지되는지 검증한다."""

    job_queue = InMemoryQueue(config=QueueConfig(default_timeout=0.05))
    event_buffer = InMemoryEventBuffer(config=EventBufferConfig(default_timeout=0.05))
    executor = ServiceExecutor(
        service=_SuccessService(),
        job_queue=job_queue,
        event_buffer=event_buffer,
        timeout_seconds=3,
    )

    queued = executor.submit_job(session_id=None, user_query="hello", context_window=20)
    payloads = [
        _extract_payload(item)
        for item in executor.stream_events(
            session_id=queued["session_id"],
            request_id=queued["request_id"],
        )
    ]
    executor.shutdown()
    types = [item["type"] for item in payloads]

    time.sleep(1)
    assert types == ["start", "token", "token", "done"]
    assert payloads[-1]["status"] == "COMPLETED"
    assert payloads[-1]["content"] == "안녕하세요"
    assert executor.get_session_status(queued["session_id"]) == "COMPLETED"


def test_service_executor_stream_service_error_emits_error() -> None:
    """서비스 예외 발생 시 error 이벤트가 송출되는지 검증한다."""

    job_queue = InMemoryQueue(config=QueueConfig(default_timeout=0.05))
    event_buffer = InMemoryEventBuffer(config=EventBufferConfig(default_timeout=0.05))
    executor = ServiceExecutor(
        service=_ErrorService(),
        job_queue=job_queue,
        event_buffer=event_buffer,
        timeout_seconds=3,
    )

    queued = executor.submit_job(session_id=None, user_query="hello", context_window=20)
    payloads = [
        _extract_payload(item)
        for item in executor.stream_events(
            session_id=queued["session_id"],
            request_id=queued["request_id"],
        )
    ]
    executor.shutdown()
    
    time.sleep(1)
    assert payloads[0]["type"] == "start"
    assert payloads[-1]["type"] == "error"
    assert payloads[-1]["status"] == "FAILED"
    assert "강제 실패" in str(payloads[-1]["error_message"] or "")
    assert executor.get_session_status(queued["session_id"]) == "FAILED"


def test_service_executor_stream_missing_done_emits_error() -> None:
    """done 이벤트 없이 종료되면 error 이벤트를 반환하는지 검증한다."""

    job_queue = InMemoryQueue(config=QueueConfig(default_timeout=0.05))
    event_buffer = InMemoryEventBuffer(config=EventBufferConfig(default_timeout=0.05))
    executor = ServiceExecutor(
        service=_NoDoneService(),
        job_queue=job_queue,
        event_buffer=event_buffer,
        timeout_seconds=3,
    )

    queued = executor.submit_job(session_id=None, user_query="hello", context_window=20)
    payloads = [
        _extract_payload(item)
        for item in executor.stream_events(
            session_id=queued["session_id"],
            request_id=queued["request_id"],
        )
    ]
    executor.shutdown()

    time.sleep(1)
    assert payloads[0]["type"] == "start"
    assert payloads[1]["type"] == "token"
    assert payloads[-1]["type"] == "error"
    assert payloads[-1]["status"] == "FAILED"
    assert executor.get_session_status(queued["session_id"]) == "FAILED"


def test_service_executor_stream_references_event() -> None:
    """references 이벤트를 허용하고 done metadata에서 references를 제거하는지 검증한다."""

    job_queue = InMemoryQueue(config=QueueConfig(default_timeout=0.05))
    event_buffer = InMemoryEventBuffer(config=EventBufferConfig(default_timeout=0.05))
    executor = ServiceExecutor(
        service=_ReferenceService(),
        job_queue=job_queue,
        event_buffer=event_buffer,
        timeout_seconds=3,
    )

    queued = executor.submit_job(session_id=None, user_query="hello", context_window=20)
    payloads = [
        _extract_payload(item)
        for item in executor.stream_events(
            session_id=queued["session_id"],
            request_id=queued["request_id"],
        )
    ]
    executor.shutdown()

    time.sleep(1)
    types = [item["type"] for item in payloads]
    assert types == ["start", "token", "references", "done"]
    references_payload = payloads[2]
    assert isinstance(references_payload["content"], str)
    decoded = json.loads(references_payload["content"])
    assert decoded[0]["type"] == "reference"
    assert decoded[0]["metadata"]["file_name"] == "manual.pdf"
    assert isinstance(payloads[-1]["metadata"], dict)
    assert "references" not in payloads[-1]["metadata"]
