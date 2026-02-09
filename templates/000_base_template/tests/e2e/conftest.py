"""
목적: Chat E2E 테스트용 서버 픽스처를 제공한다.
설명: pytest 실행 중 uvicorn 서버를 실제 프로세스로 기동/종료하고 HTTP 클라이언트를 제공한다.
디자인 패턴: 테스트 픽스처 패턴
참조: src/base_template/api/main.py
"""

from __future__ import annotations

import os
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import httpx
import pytest


@dataclass(frozen=True)
class ChatServerContext:
    """E2E 서버 실행 컨텍스트."""

    base_url: str
    chat_db_path: Path


def _find_free_port() -> int:
    """사용 가능한 로컬 포트를 반환한다."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server_ready(
    process: subprocess.Popen[str],
    base_url: str,
    timeout_seconds: float = 20.0,
) -> None:
    """서버 헬스체크 응답이 가능할 때까지 대기한다."""

    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=1)
            raise RuntimeError(
                "E2E 서버가 초기화 전에 종료되었습니다.\n"
                f"stdout:\n{stdout[-500:]}\n"
                f"stderr:\n{stderr[-500:]}"
            )
        try:
            response = httpx.get(f"{base_url}/health", timeout=1.0)
            if response.status_code == 200:
                return
        except Exception as error:  # noqa: BLE001 - 재시도 루프 유지
            last_error = error
        time.sleep(0.2)
    raise RuntimeError(f"E2E 서버 기동 대기 타임아웃: {last_error}")


@pytest.fixture(scope="session")
def chat_server_context() -> Iterator[ChatServerContext]:
    """Chat API 서버를 실제 프로세스로 띄운 뒤 컨텍스트를 반환한다."""

    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        pytest.skip("Gemini E2E 테스트를 위해 GEMINI_API_KEY 또는 GOOGLE_API_KEY가 필요합니다.")

    root = Path(__file__).resolve().parents[2]
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    tmp_dir = tempfile.TemporaryDirectory(prefix="chat-e2e-")
    chat_db_path = Path(tmp_dir.name) / "chat_history.sqlite"

    command = [
        "uv",
        "run",
        "uvicorn",
        "base_template.api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    env = os.environ.copy()
    env["CHAT_DB_PATH"] = str(chat_db_path)
    env["CHAT_LLM_PROVIDER"] = "gemini"
    env["GEMINI_MODEL"] = env.get("GEMINI_MODEL", "gemini-2.5-flash")
    env["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        command,
        cwd=str(root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_server_ready(process=process, base_url=base_url)
        yield ChatServerContext(base_url=base_url, chat_db_path=chat_db_path)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        process.communicate(timeout=1)
        tmp_dir.cleanup()


@pytest.fixture
def chat_api_client(chat_server_context: ChatServerContext) -> Iterator[httpx.Client]:
    """Chat API 호출용 HTTP 클라이언트를 반환한다."""

    with httpx.Client(base_url=chat_server_context.base_url, timeout=10.0) as client:
        yield client
