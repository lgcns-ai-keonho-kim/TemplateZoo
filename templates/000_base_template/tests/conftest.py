"""
목적: pytest 공통 로깅 훅을 제공한다.
설명: 테스트 시작/종료와 결과를 로깅해 실행 흐름을 추적한다.
디자인 패턴: 테스트 훅
참조: pyproject.toml
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv


_LOGGER = logging.getLogger("tests")


def _load_env_files() -> None:
    """환경 변수 파일을 로딩한다."""

    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
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

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PW")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DATABASE")
    if not all([user, password, host, port, database]):
        return None
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def _build_mongodb_uri() -> str | None:
    """MongoDB URI를 조합한다."""

    host = os.getenv("MONGODB_HOST", "127.0.0.1")
    port = os.getenv("MONGODB_PORT", "27017")
    user = os.getenv("MONGODB_USER")
    password = os.getenv("MONGODB_PW")
    if user and password:
        return f"mongodb://{user}:{password}@{host}:{port}"
    return f"mongodb://{host}:{port}"


def _build_redis_url() -> str | None:
    """Redis URL을 조합한다."""

    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PW")
    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"




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
    _set_if_missing("REDIS_URL", _build_redis_url())
    _set_if_missing("ELASTICSEARCH_HOSTS", _build_elasticsearch_hosts())


_load_env_files()
_prepare_default_env()


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
