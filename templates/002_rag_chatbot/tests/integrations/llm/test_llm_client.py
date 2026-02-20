"""
목적: LLM 클라이언트 로깅 동작을 검증한다.
설명: 파일/메모리 로깅과 스트리밍 로그 기록을 테스트한다.
디자인 패턴: 프록시 패턴 테스트
참조: src/rag_chatbot/integrations/llm/client.py
"""

from __future__ import annotations

import os

from rag_chatbot.integrations.fs import FileLogRepository
from rag_chatbot.integrations.llm import LLMClient
from rag_chatbot.shared.logging import InMemoryLogger


def _build_openai_model(*, streaming: bool):
    """환경 변수 기반으로 OpenAI 모델을 생성한다."""

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("LLM 테스트를 위해 OPENAI_API_KEY가 필요합니다.")
    model_name = (os.getenv("OPENAI_MODEL") or "").strip()
    if not model_name:
        raise RuntimeError("LLM 테스트를 위해 OPENAI_MODEL이 필요합니다.")
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as error:
        raise RuntimeError("LLM 테스트를 위해 langchain-openai 패키지가 필요합니다.") from error

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        streaming=streaming,
    )


def test_llm_client_file_logging(tmp_path):
    """파일 저장소에 로그가 기록되는지 확인한다."""

    repository = FileLogRepository(base_dir=str(tmp_path))
    model = _build_openai_model(streaming=False)
    client = LLMClient(model=model, logging_engine=repository, name="openai-model")

    client.invoke("hello")

    print(f"[llm-test] 로그 저장 경로: {repository.base_dir}")
    records = repository.list()
    for record in records:
        print(
            "[llm-test] 로그 레코드",
            f"level={record.level}",
            f"message={record.message}",
            f"timestamp={record.timestamp.isoformat()}",
            f"metadata={record.metadata}",
        )
    assert records
    assert any(record.metadata.get("model_name") == "openai-model" for record in records)


def test_llm_client_stream_background_logging():
    """스트리밍 성공 로그가 백그라운드 러너로 기록되는지 확인한다."""

    logger = InMemoryLogger(name="llm-test")

    def inline_runner(fn, *args):
        fn(*args)

    model = _build_openai_model(streaming=True)
    client = LLMClient(
        model=model,
        logging_engine=logger,
        background_runner=inline_runner,
    )

    for chunk in client.stream("hello"):
        text = getattr(chunk, "content", None)
        if text is None:
            text = str(chunk)
        print(text, end="", flush=True)
    print()

    records = logger.repository.list()
    assert any(record.metadata.get("success") is True for record in records)
    assert any(record.metadata.get("action") == "stream" for record in records)
