"""
목적: 애플리케이션 설정 로더를 제공한다.
설명: dict/JSON 파일/환경 변수를 병합해 설정을 생성한다.
디자인 패턴: 빌더 패턴
참조: src/rag_chatbot/shared/logging/logger.py, src/rag_chatbot/shared/const/__init__.py
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Mapping, Optional

from rag_chatbot.shared.const import SharedConst
from rag_chatbot.shared.logging import Logger, create_default_logger


class ConfigLoader:
    """설정 로더 구현체이다.

    Args:
        logger: 주입 가능한 로거.
    """

    _DEFAULT_ENCODING = SharedConst.DEFAULT_ENCODING
    _DEFAULT_ENV_DELIMITER = SharedConst.ENV_NESTED_DELIMITER

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self._logger = logger or create_default_logger("ConfigLoader")
        self._sources: list[Dict[str, Any]] = []

    def add_dict(self, data: Optional[Mapping[str, Any]]) -> "ConfigLoader":
        """딕셔너리 설정을 추가한다."""

        if not data:
            return self
        self._sources.append(dict(data))
        return self

    def add_json_file(
        self,
        path: str,
        required: bool = False,
        encoding: Optional[str] = None,
    ) -> "ConfigLoader":
        """JSON 파일 설정을 추가한다."""

        if not path:
            raise ValueError("path는 비어 있을 수 없습니다.")
        if not os.path.exists(path):
            if required:
                raise FileNotFoundError(path)
            self._logger.warning(f"설정 파일이 없어 건너뜁니다: {path}")
            return self
        encoding = encoding or self._DEFAULT_ENCODING
        with open(path, "r", encoding=encoding) as handle:
            try:
                payload = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError("JSON 설정 파일 파싱에 실패했습니다.") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON 설정 파일은 최상위가 객체여야 합니다.")
        self._sources.append(payload)
        return self

    def add_env(
        self,
        prefix: str = "",
        delimiter: Optional[str] = None,
        lowercase_keys: bool = True,
    ) -> "ConfigLoader":
        """환경 변수 설정을 추가한다."""

        delimiter = delimiter or self._DEFAULT_ENV_DELIMITER
        env_data: Dict[str, Any] = {}
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            trimmed = key[len(prefix) :] if prefix else key
            if not trimmed:
                continue
            parts = trimmed.split(delimiter) if delimiter else [trimmed]
            parts = [part for part in parts if part]
            if lowercase_keys:
                parts = [part.lower() for part in parts]
            if not parts:
                continue
            self._assign_nested(env_data, parts, self._parse_value(value))
        if env_data:
            self._sources.append(env_data)
        return self

    def build(self, overrides: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """수집된 설정을 병합해 반환한다."""

        merged: Dict[str, Any] = {}
        for source in self._sources:
            merged = self._merge(merged, source)
        if overrides:
            merged = self._merge(merged, dict(overrides))
        return merged

    def _assign_nested(self, root: Dict[str, Any], keys: list[str], value: Any) -> None:
        current = root
        for part in keys[:-1]:
            if part not in current or not isinstance(current.get(part), dict):
                current[part] = {}
            current = current[part]
        current[keys[-1]] = value

    def _merge(self, base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(base)
        for key, value in incoming.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _parse_value(self, raw: str) -> Any:
        lowered = raw.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        if lowered in {"null", "none"}:
            return None
        try:
            if "." in raw:
                return float(raw)
            return int(raw)
        except ValueError:
            pass
        if (raw.startswith("{") and raw.endswith("}")) or (
            raw.startswith("[") and raw.endswith("]")
        ):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        return raw
