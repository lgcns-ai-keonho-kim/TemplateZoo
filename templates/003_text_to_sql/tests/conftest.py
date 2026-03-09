"""
목적: 테스트 공통 환경/픽스처/로깅 훅을 단일화해 제공한다.
설명: .env 로딩, DB 기본 env 준비, Gemini LLM 팩토리, Chat E2E 서버 fixture를 함께 제공한다.
디자인 패턴: 테스트 픽스처 + 테스트 훅
참조: tests/e2e/test_chat_api_server_e2e.py, pyproject.toml
"""

from __future__ import annotations

import logging
import os
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator

import httpx
import pytest
from dotenv import load_dotenv

if TYPE_CHECKING:
    from text_to_sql.integrations.llm import LLMClient


_LOGGER = logging.getLogger("tests")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_E2E_CLIENT_TIMEOUT = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)


def _load_env_files() -> None:
    """환경 변수 파일을 로딩한다."""

    env_path = _PROJECT_ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError(".env 파일이 필요합니다. 프로젝트 루트에 .env.sample을 참고해서 .env를 생성해주세요.")

    load_dotenv(env_path, override=False)


def _set_if_missing(key: str, value: str | None) -> None:
    """환경 변수가 없을 때만 값을 설정한다."""

    if not value:
        return
    if not os.getenv(key):
        os.environ[key] = value


def _build_postgres_dsn() -> str | None:
    """PostgreSQL DSN을 조합한다."""

    database = _allowlist_connection_value(engine_name="postgres", key="database")

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PW")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    if not all([user, password, host, port, database]):
        return None
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def _build_mongodb_uri() -> str | None:
    """MongoDB URI를 조합한다."""

    host = os.getenv("MONGODB_HOST", "127.0.0.1")
    port = os.getenv("MONGODB_PORT", "27017")
    user = os.getenv("MONGODB_USER")
    password = os.getenv("MONGODB_PW")
    auth_db = os.getenv("MONGODB_AUTH_DB")
    if user and password:
        base = f"mongodb://{user}:{password}@{host}:{port}"
        if auth_db:
            return f"{base}/?authSource={auth_db}"
        return base
    return f"mongodb://{host}:{port}"


def _allowlist_connection_value(*, engine_name: str, key: str) -> str | None:
    """table_allowlist 파일에서 엔진별 connection 값을 조회한다."""

    try:
        from text_to_sql.core.chat.utils import load_table_allowlist_config
    except Exception:
        return None

    try:
        config = load_table_allowlist_config(project_root=_PROJECT_ROOT)
    except Exception:
        return None

    raw_targets = config.get("targets")
    if not isinstance(raw_targets, list):
        return None

    wanted_engine = engine_name.strip().lower()
    wanted_key = key.strip()
    for target in raw_targets:
        if not isinstance(target, dict):
            continue
        engine = str(target.get("engine") or "").strip().lower()
        if engine != wanted_engine:
            continue
        connection = target.get("connection")
        if not isinstance(connection, dict):
            continue
        value = str(connection.get(wanted_key) or "").strip()
        if value:
            return value
    return None


def _build_elasticsearch_hosts() -> str | None:
    """Elasticsearch HOSTS 문자열을 조합한다."""

    host = os.getenv("ELASTICSEARCH_HOST", "127.0.0.1")
    port = os.getenv("ELASTICSEARCH_PORT", "9200")
    scheme = os.getenv("ELASTICSEARCH_SCHEME", "http")
    if not host or not port or not scheme:
        return None
    return f"{scheme}://{host}:{port}"


def _prepare_default_env() -> None:
    """테스트 기본 환경 변수를 준비한다."""

    _set_if_missing("POSTGRES_DSN", _build_postgres_dsn())
    _set_if_missing("MONGODB_URI", _build_mongodb_uri())
    _set_if_missing("ELASTICSEARCH_HOSTS", _build_elasticsearch_hosts())


_load_env_files()
_prepare_default_env()


@dataclass(frozen=True)
class ChatServerContext:
    """E2E 서버 실행 컨텍스트."""

    base_url: str
    chat_db_path: Path


@dataclass(frozen=True)
class GeminiRuntimeConfig:
    """Gemini 런타임 설정 컨텍스트."""

    model: str
    project: str


def _find_free_port() -> int:
    """사용 가능한 로컬 포트를 반환한다."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server_ready(
    process: subprocess.Popen[str],
    base_url: str,
    timeout_seconds: float = 30.0,
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


def _require_env_value(key: str) -> str:
    """필수 환경 변수를 검증해 반환한다."""

    value = (os.getenv(key) or "").strip()
    if not value:
        raise RuntimeError(f"테스트를 위해 {key} 환경 변수가 필요합니다.")
    return value


def _build_gemini_model(config: GeminiRuntimeConfig):
    """Gemini 모델 클라이언트를 생성한다."""

    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=config.model,
        project=config.project,
        thinking_level="minimal",
    )


@pytest.fixture(scope="session")
def gemini_runtime_config() -> GeminiRuntimeConfig:
    """Gemini 테스트 런타임 설정을 반환한다."""

    return GeminiRuntimeConfig(
        model=_require_env_value("GEMINI_MODEL"),
        project=_require_env_value("GEMINI_PROJECT"),
    )


@pytest.fixture(scope="session")
def gemini_llm_client_factory(
    gemini_runtime_config: GeminiRuntimeConfig,
) -> Callable[..., LLMClient]:
    """Gemini 기반 LLMClient 생성 팩토리를 반환한다."""

    from text_to_sql.integrations.llm import LLMClient

    def _factory(
        *,
        name: str = "gemini-test-llm",
        logging_engine: object | None = None,
        background_runner: Callable[..., None] | None = None,
    ) -> LLMClient:
        kwargs: dict[str, object] = {
            "model": _build_gemini_model(gemini_runtime_config),
            "name": name,
        }
        if logging_engine is not None:
            kwargs["logging_engine"] = logging_engine
        if background_runner is not None:
            kwargs["background_runner"] = background_runner
        return LLMClient(**kwargs)

    return _factory


@pytest.fixture(scope="session")
def chat_server_context(
    gemini_runtime_config: GeminiRuntimeConfig,
) -> Iterator[ChatServerContext]:
    """Chat API 서버를 실제 프로세스로 띄운 뒤 컨텍스트를 반환한다."""

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    tmp_dir = tempfile.TemporaryDirectory(prefix="chat-e2e-")
    chat_db_path = Path(tmp_dir.name) / "chat_history.sqlite"

    command = [
        "uv",
        "run",
        "uvicorn",
        "text_to_sql.api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    env = os.environ.copy()
    env["CHAT_DB_PATH"] = str(chat_db_path)
    env["GEMINI_PROJECT"] = gemini_runtime_config.project
    env["GEMINI_MODEL"] = gemini_runtime_config.model
    env["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        command,
        cwd=str(_PROJECT_ROOT),
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
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
        tmp_dir.cleanup()


@pytest.fixture
def chat_api_client(chat_server_context: ChatServerContext) -> Iterator[httpx.Client]:
    """Chat API 호출용 HTTP 클라이언트를 반환한다."""

    with httpx.Client(base_url=chat_server_context.base_url, timeout=_E2E_CLIENT_TIMEOUT) as client:
        yield client


def pytest_sessionstart(session) -> None:  # noqa: D401 - pytest 훅 시그니처 유지
    """테스트 세션 시작을 로깅한다."""

    _LOGGER.info("테스트 세션 시작")


def pytest_sessionfinish(session, exitstatus: int) -> None:  # noqa: D401 - pytest 훅 시그니처 유지
    """테스트 세션 종료를 로깅한다."""

    _LOGGER.info("테스트 세션 종료 (exitstatus=%s)", exitstatus)


def pytest_runtest_logstart(nodeid: str, location) -> None:  # noqa: D401 - pytest 훅 시그니처 유지
    """각 테스트 시작을 로깅한다."""

    _LOGGER.info("테스트 시작: %s", nodeid)


def pytest_runtest_logreport(report) -> None:  # noqa: D401 - pytest 훅 시그니처 유지
    """테스트 결과를 로깅한다."""

    if report.when != "call":
        return
    if report.passed:
        _LOGGER.info("테스트 완료: %s", report.nodeid)
        return
    if report.skipped:
        _LOGGER.warning("테스트 스킵: %s", report.nodeid)
        return
    _LOGGER.error("테스트 실패: %s", report.nodeid)
