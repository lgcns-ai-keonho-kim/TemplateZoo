"""
목적: LLM 클라이언트 로깅 동작을 검증한다.
설명: conftest의 Gemini 공통 팩토리를 사용해 invoke/stream 로깅 핵심 흐름을 검증한다.
디자인 패턴: 프록시 패턴 테스트
참조: tests/conftest.py, src/one_shot_agent/integrations/llm/client.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from one_shot_agent.integrations.fs import FileLogRepository
from one_shot_agent.shared.logging import InMemoryLogger

if TYPE_CHECKING:
    from one_shot_agent.integrations.llm import LLMClient


def test_llm_client_file_logging(
    tmp_path,
    gemini_llm_client_factory: Callable[..., LLMClient],
) -> None:
    """파일 저장소에 로그가 기록되는지 확인한다."""

    repository = FileLogRepository(base_dir=str(tmp_path))
    client = gemini_llm_client_factory(
        logging_engine=repository,
        name="gemini-file-llm",
    )

    client.invoke("hello")

    records = repository.list()
    assert records
    assert any(record.metadata.get("action") == "invoke" for record in records)
    assert any(record.metadata.get("success") is True for record in records)
    assert any(record.metadata.get("model_name") == "gemini-file-llm" for record in records)


def test_llm_client_stream_background_logging(
    gemini_llm_client_factory: Callable[..., LLMClient],
) -> None:
    """스트리밍 성공 로그가 백그라운드 러너로 기록되는지 확인한다."""

    logger = InMemoryLogger(name="llm-test")

    def inline_runner(fn, *args) -> None:
        fn(*args)

    client = gemini_llm_client_factory(
        logging_engine=logger,
        name="gemini-stream-llm",
        background_runner=inline_runner,
    )

    for _ in client.stream("hello"):
        pass

    records = logger.repository.list()
    assert any(record.metadata.get("success") is True for record in records)
    assert any(record.metadata.get("action") == "stream" for record in records)
    assert any(record.metadata.get("model_name") == "gemini-stream-llm" for record in records)
