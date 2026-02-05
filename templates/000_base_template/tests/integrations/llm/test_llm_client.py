"""
목적: LLM 클라이언트 로깅 동작을 검증한다.
설명: 파일/메모리 로깅과 스트리밍 로그 기록을 테스트한다.
디자인 패턴: 프록시 패턴 테스트
참조: src/base_template/integrations/llm/client.py
"""

from __future__ import annotations

import inspect
import os
from typing import Any

from base_template.integrations.fs import FileLogRepository
from base_template.integrations.llm import LLMClient
from base_template.shared.logging import InMemoryLogger


def _build_gemini_model(*, streaming: bool):
    """환경 변수 기반으로 Gemini 모델을 생성한다."""

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        import pytest

        pytest.skip("GEMINI_API_KEY 또는 GOOGLE_API_KEY가 필요합니다.")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        import pytest

        pytest.skip("langchain-google-genai 패키지가 필요합니다.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # 스트리밍 옵션을 조건부로 추가하므로 값 타입을 넓게 잡는다.
    kwargs: dict[str, Any] = {"model": model_name}
    signature = inspect.signature(ChatGoogleGenerativeAI)
    if streaming and "streaming" in signature.parameters:
        kwargs["streaming"] = True
    return ChatGoogleGenerativeAI(**kwargs)


def test_llm_client_file_logging(tmp_path):
    """파일 저장소에 로그가 기록되는지 확인한다."""

    repository = FileLogRepository(base_dir=str(tmp_path))
    model = _build_gemini_model(streaming=False)
    client = LLMClient(model=model, logging_engine=repository, name="gemini-model")

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
    assert any(record.metadata.get("model_name") == "gemini-model" for record in records)


def test_llm_client_stream_background_logging():
    """스트리밍 성공 로그가 백그라운드 러너로 기록되는지 확인한다."""

    logger = InMemoryLogger(name="llm-test")

    def inline_runner(fn, *args):
        fn(*args)

    model = _build_gemini_model(streaming=True)
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
