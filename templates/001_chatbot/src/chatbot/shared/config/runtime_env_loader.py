"""
목적: 런타임 환경별 `.env` 로딩을 제공한다.
설명: 기본 `.env`를 로드한 뒤 `ENV` 값을 기준으로 local/dev/stg/prod 환경 파일을 선택해 로드한다.
디자인 패턴: 전략 패턴
참조: src/chatbot/shared/config/loader.py, src/chatbot/api/main.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv

from chatbot.shared.logging import Logger, create_default_logger


class RuntimeEnvironmentLoader:
    """런타임 환경별 `.env` 로더이다.

    동작 순서:
    1. 프로젝트 루트의 `.env`를 우선 로드한다.
    2. `ENV`(또는 후보 키) 값을 읽어 런타임 환경을 결정한다.
    3. 값이 비어 있으면 `local`로 간주한다.
    4. `dev/stg/prod`인 경우 `src/chatbot/resources/<env>/.env`를 로드한다.
    """

    _SUPPORTED_ENVS = {"local", "dev", "stg", "prod"}
    _ENV_ALIASES = {
        "development": "dev",
        "staging": "stg",
        "production": "prod",
    }
    _DEFAULT_ENV_KEY_CANDIDATES = ("ENV", "APP_ENV", "APP_STAGE")
    _RESOURCE_ENV_FILENAME = ".env"

    def __init__(
        self,
        logger: Optional[Logger] = None,
        project_root: Optional[Path] = None,
        resources_root: Optional[Path] = None,
        env_key_candidates: Optional[Sequence[str]] = None,
    ) -> None:
        module_path = Path(__file__).resolve()
        default_project_root = module_path.parents[4]
        default_resources_root = module_path.parents[2] / "resources"
        self._project_root = Path(project_root or default_project_root)
        self._resources_root = Path(resources_root or default_resources_root)
        self._root_env_path = self._project_root / ".env"
        self._env_key_candidates = tuple(
            env_key_candidates or self._DEFAULT_ENV_KEY_CANDIDATES
        )
        self._logger = logger or create_default_logger("RuntimeEnvironmentLoader")

    @property
    def project_root(self) -> Path:
        """프로젝트 루트 경로를 반환한다."""

        return self._project_root

    @property
    def resources_root(self) -> Path:
        """환경 리소스 루트 경로를 반환한다."""

        return self._resources_root

    def load(self, override_root_env: bool = False) -> str:
        """런타임 환경을 판별하고 관련 `.env`를 로드한다.

        Args:
            override_root_env: 루트 `.env`가 기존 환경 변수를 덮어쓸지 여부.

        Returns:
            판별된 런타임 환경 문자열(`local/dev/stg/prod`).
        """

        self._load_root_env(override=override_root_env)
        runtime_env = self._resolve_runtime_env()
        os.environ["ENV"] = runtime_env

        if runtime_env == "local":
            self._logger.info(
                f"런타임 환경 로드 완료: env={runtime_env}, root={self._root_env_path}"
            )
            return runtime_env

        selected_env_file = self._resolve_resource_env_file(runtime_env=runtime_env)
        load_dotenv(dotenv_path=selected_env_file, override=False)
        self._logger.info(
            f"런타임 환경 로드 완료: env={runtime_env}, resource={selected_env_file}"
        )
        return runtime_env

    def _load_root_env(self, override: bool) -> None:
        if not self._root_env_path.exists():
            self._logger.warning(
                f"프로젝트 루트 .env 파일이 없어 건너뜁니다: {self._root_env_path}"
            )
            return
        load_dotenv(dotenv_path=self._root_env_path, override=override)

    def _resolve_runtime_env(self) -> str:
        raw_value = self._read_env_value_from_candidates()
        if raw_value is None:
            return "local"

        normalized = raw_value.strip().lower()
        if not normalized:
            return "local"
        normalized = self._ENV_ALIASES.get(normalized, normalized)
        if normalized not in self._SUPPORTED_ENVS:
            supported_values = ", ".join(sorted(self._SUPPORTED_ENVS))
            raise ValueError(
                f"지원하지 않는 ENV 값입니다: {raw_value}. "
                f"허용값: {supported_values}"
            )
        return normalized

    def _read_env_value_from_candidates(self) -> str | None:
        for key in self._env_key_candidates:
            key_candidates = (key, key.lower())
            for candidate in key_candidates:
                value = os.getenv(candidate)
                if value and value.strip():
                    return value
        return None

    def _resolve_resource_env_file(self, runtime_env: str) -> Path:
        env_dir = self._resources_root / runtime_env
        if not env_dir.exists():
            raise FileNotFoundError(
                f"환경 리소스 디렉터리를 찾을 수 없습니다: {env_dir}"
            )

        candidate = env_dir / self._RESOURCE_ENV_FILENAME
        if candidate.exists():
            return candidate
        raise FileNotFoundError(
            f"환경 파일을 찾을 수 없습니다: {candidate}"
        )
