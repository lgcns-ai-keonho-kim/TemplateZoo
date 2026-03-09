"""
목적: Text-to-SQL 테이블 allowlist 로더를 제공한다.
설명: 프로젝트 루트의 allowlist 파일(YAML)을 로드하고 env 참조를 실제 연결값으로 해석한다.
디자인 패턴: 로더 + 검증기
참조: src/text_to_sql/api/main.py, src/text_to_sql/core/chat/state/graph_state.py
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from text_to_sql.shared.exceptions import BaseAppException, ExceptionDetail
from text_to_sql.shared.logging import Logger, create_default_logger

_ALLOWLIST_FILE_CANDIDATES = (
    "table_allowlist.yaml",
    "table_allowlist.yml",
)
_ALLOWLIST_FILE_SUFFIXES = {".yaml", ".yml"}
_ALLOWLIST_FILE_ENV_KEY = "TABLE_ALLOWLIST_FILE"
_DEFAULT_POSTGRES_PORT = 5432
_DEFAULT_MONGODB_PORT = 27017


def load_table_allowlist_config(
    *,
    project_root: Path | None = None,
    logger: Logger | None = None,
) -> dict[str, object]:
    """프로젝트 루트 allowlist 파일을 로드하고 정규화한다."""

    loader_logger = logger or create_default_logger("TableAllowlistLoader")
    root = (
        Path(project_root)
        if project_root is not None
        else Path(__file__).resolve().parents[4]
    )
    allowlist_path = _resolve_allowlist_path(root)
    raw = _read_allowlist_file(allowlist_path)
    normalized = _normalize_allowlist(raw=raw, source_path=allowlist_path)
    target_count = 0
    loaded_targets = normalized.get("targets")
    if isinstance(loaded_targets, list):
        target_count = len(loaded_targets)
    loader_logger.info(
        "table_allowlist 로드 완료: source=%s, targets=%s"
        % (allowlist_path, target_count)
    )
    return normalized


def _resolve_allowlist_path(project_root: Path) -> Path:
    """허용된 확장자 목록에서 allowlist 파일 경로를 결정한다."""

    explicit_path = _optional_string(os.getenv(_ALLOWLIST_FILE_ENV_KEY))
    if explicit_path:
        explicit_candidate = Path(explicit_path)
        if not explicit_candidate.is_absolute():
            explicit_candidate = project_root / explicit_candidate
        if not explicit_candidate.exists() or not explicit_candidate.is_file():
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_NOT_FOUND",
                cause=f"{_ALLOWLIST_FILE_ENV_KEY}={explicit_path}",
                hint="TABLE_ALLOWLIST_FILE에 지정한 파일 경로를 확인하세요.",
            )
            raise BaseAppException("테이블 allowlist 파일을 찾을 수 없습니다.", detail)
        suffix = explicit_candidate.suffix.lower()
        if suffix not in _ALLOWLIST_FILE_SUFFIXES:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_FORMAT_UNSUPPORTED",
                cause=f"source={explicit_candidate}",
                hint="TABLE_ALLOWLIST_FILE은 .yaml/.yml 파일만 지원합니다.",
            )
            raise BaseAppException("지원하지 않는 allowlist 파일 형식입니다.", detail)
        return explicit_candidate

    found_paths: list[Path] = []
    for filename in _ALLOWLIST_FILE_CANDIDATES:
        path = project_root / filename
        if path.exists() and path.is_file():
            found_paths.append(path)

    if not found_paths:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_NOT_FOUND",
            cause=f"project_root={project_root}",
            hint=(
                f"{_ALLOWLIST_FILE_ENV_KEY}를 지정하거나, "
                "프로젝트 루트에 table_allowlist.yaml(.yml) 파일을 생성하세요."
            ),
        )
        raise BaseAppException("테이블 allowlist 파일을 찾을 수 없습니다.", detail)

    if len(found_paths) > 1:
        joined = ", ".join(str(path.name) for path in found_paths)
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_AMBIGUOUS",
            cause=f"multiple_files={joined}",
            hint="allowlist 파일은 하나만 유지하세요.",
        )
        raise BaseAppException("테이블 allowlist 파일이 중복되었습니다.", detail)

    return found_paths[0]


def _read_allowlist_file(path: Path) -> object:
    """파일 확장자에 맞춰 allowlist를 파싱한다."""

    suffix = path.suffix.lower()
    raw_text = path.read_text(encoding="utf-8")
    try:
        if suffix in _ALLOWLIST_FILE_SUFFIXES:
            import yaml

            return yaml.safe_load(raw_text)
    except BaseAppException:
        raise
    except Exception as error:  # noqa: BLE001 - 파일 파싱 오류를 도메인 예외로 래핑
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_PARSE_ERROR",
            cause=f"source={path}",
            metadata={"error": repr(error)},
        )
        raise BaseAppException(
            "테이블 allowlist 파일 파싱에 실패했습니다.", detail, error
        ) from error

    detail = ExceptionDetail(
        code="TABLE_ALLOWLIST_FORMAT_UNSUPPORTED",
        cause=f"source={path}",
        hint="지원 확장자는 .yaml/.yml 입니다.",
    )
    raise BaseAppException("지원하지 않는 allowlist 파일 형식입니다.", detail)


def _normalize_allowlist(*, raw: object, source_path: Path) -> dict[str, object]:
    """allowlist 원본 객체를 내부 표준 구조로 정규화한다."""

    raw_map = _to_string_key_dict(raw)
    if raw_map is None:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID",
            cause="루트 객체는 mapping이어야 합니다.",
            metadata={"source": str(source_path)},
        )
        raise BaseAppException("테이블 allowlist 형식이 올바르지 않습니다.", detail)

    raw_version = raw_map.get("version", 1)
    version = _to_positive_int(raw_version, default=1, field_name="version")

    raw_targets = raw_map.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID",
            cause="targets 목록이 비어 있거나 리스트가 아닙니다.",
            metadata={"source": str(source_path)},
        )
        raise BaseAppException("테이블 allowlist 형식이 올바르지 않습니다.", detail)

    normalized_targets: list[dict[str, object]] = []
    seen_aliases: set[str] = set()
    for index, target in enumerate(raw_targets):
        normalized = _normalize_target(
            target=target, index=index, source_path=source_path
        )
        alias = str(normalized["alias"])
        if alias in seen_aliases:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_DUPLICATED_ALIAS",
                cause=f"alias={alias}",
                metadata={"source": str(source_path)},
            )
            raise BaseAppException("target alias가 중복되었습니다.", detail)
        seen_aliases.add(alias)
        normalized_targets.append(normalized)

    return {
        "version": version,
        "source_file": str(source_path),
        "targets": normalized_targets,
    }


def _normalize_target(
    *, target: object, index: int, source_path: Path
) -> dict[str, object]:
    """target 1건을 정규화한다."""

    target_map = _to_string_key_dict(target)
    if target_map is None:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_TARGET",
            cause=f"targets[{index}]는 mapping이어야 합니다.",
            metadata={"source": str(source_path)},
        )
        raise BaseAppException(
            "테이블 allowlist target 형식이 올바르지 않습니다.", detail
        )

    alias = _required_string(target_map, key="alias", parent=f"targets[{index}]")
    engine = _required_string(
        target_map, key="engine", parent=f"targets[{index}]"
    ).lower()

    raw_connection = _to_string_key_dict(target_map.get("connection"))
    if raw_connection is None:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_CONNECTION",
            cause=f"targets[{index}].connection은 mapping이어야 합니다.",
            metadata={"source": str(source_path)},
        )
        raise BaseAppException("connection 형식이 올바르지 않습니다.", detail)
    connection = _resolve_connection(
        connection=raw_connection,
        engine=engine,
        alias=alias,
        source_path=source_path,
    )

    raw_allowlist = _to_string_key_dict(target_map.get("allowlist"))
    if raw_allowlist is None:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_ALLOWLIST",
            cause=f"targets[{index}].allowlist는 mapping이어야 합니다.",
            metadata={"source": str(source_path), "alias": alias},
        )
        raise BaseAppException("allowlist 형식이 올바르지 않습니다.", detail)

    tables = _normalize_tables(
        raw_tables=raw_allowlist.get("tables"),
        alias=alias,
        source_path=source_path,
    )

    return {
        "alias": alias,
        "engine": engine,
        "connection": connection,
        "allowlist": {"tables": tables},
    }


def _resolve_connection(
    *,
    connection: dict[str, Any],
    engine: str,
    alias: str,
    source_path: Path,
) -> dict[str, object]:
    """connection 블록에서 env 참조를 실제 값으로 해석한다."""

    resolved: dict[str, object] = {}

    dsn = _resolve_string(
        connection, value_key="dsn", env_key_key="dsn_env", required=False
    )
    if dsn:
        resolved["dsn"] = dsn

    if engine == "postgres":
        if not dsn:
            resolved["host"] = _resolve_string(
                connection,
                value_key="host",
                env_key_key="host_env",
                required=True,
            )
            resolved["port"] = _resolve_int(
                connection,
                value_key="port",
                env_key_key="port_env",
                required=True,
                default=_DEFAULT_POSTGRES_PORT,
            )
            resolved["user"] = _resolve_string(
                connection,
                value_key="user",
                env_key_key="user_env",
                required=True,
            )
            resolved["password"] = _resolve_string(
                connection,
                value_key="password",
                env_key_key="password_env",
                required=False,
            )
        resolved["database"] = _resolve_string(
            connection,
            value_key="database",
            env_key_key="database_env",
            required=True,
        )
        schema = _resolve_string(
            connection,
            value_key="schema",
            env_key_key="schema_env",
            required=False,
        )
        resolved["schema"] = schema or "public"
        return resolved

    if engine == "mongodb":
        if not dsn:
            resolved["host"] = _resolve_string(
                connection,
                value_key="host",
                env_key_key="host_env",
                required=True,
            )
            resolved["port"] = _resolve_int(
                connection,
                value_key="port",
                env_key_key="port_env",
                required=True,
                default=_DEFAULT_MONGODB_PORT,
            )
            resolved["user"] = _resolve_string(
                connection,
                value_key="user",
                env_key_key="user_env",
                required=False,
            )
            resolved["password"] = _resolve_string(
                connection,
                value_key="password",
                env_key_key="password_env",
                required=False,
            )
        resolved["database"] = _resolve_string(
            connection,
            value_key="database",
            env_key_key="database_env",
            required=True,
        )
        resolved["auth_source"] = _resolve_string(
            connection,
            value_key="auth_source",
            env_key_key="auth_source_env",
            required=False,
        )
        return resolved

    if engine == "sqlite":
        resolved["path"] = _resolve_string(
            connection,
            value_key="path",
            env_key_key="path_env",
            required=True,
        )
        return resolved

    detail = ExceptionDetail(
        code="TABLE_ALLOWLIST_ENGINE_UNSUPPORTED",
        cause=f"alias={alias}, engine={engine}",
        metadata={"source": str(source_path)},
    )
    raise BaseAppException("지원하지 않는 allowlist target engine입니다.", detail)


def _normalize_tables(
    *, raw_tables: object, alias: str, source_path: Path
) -> list[dict[str, object]]:
    """allowlist 테이블 목록을 정규화한다."""

    if not isinstance(raw_tables, list) or not raw_tables:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_TABLES",
            cause=f"alias={alias}, allowlist.tables는 비어 있지 않은 리스트여야 합니다.",
            metadata={"source": str(source_path)},
        )
        raise BaseAppException("allowlist tables 형식이 올바르지 않습니다.", detail)

    tables: list[dict[str, object]] = []
    seen_table_names: set[str] = set()
    for table_index, raw_table in enumerate(raw_tables):
        table_map = _to_string_key_dict(raw_table)
        if table_map is None:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_INVALID_TABLE",
                cause=f"alias={alias}, tables[{table_index}]는 mapping이어야 합니다.",
                metadata={"source": str(source_path)},
            )
            raise BaseAppException("allowlist table 형식이 올바르지 않습니다.", detail)

        table_name = _required_string(
            table_map, key="name", parent=f"{alias}.tables[{table_index}]"
        )
        if table_name in seen_table_names:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_DUPLICATED_TABLE",
                cause=f"alias={alias}, table={table_name}",
                metadata={"source": str(source_path)},
            )
            raise BaseAppException("allowlist table 이름이 중복되었습니다.", detail)
        seen_table_names.add(table_name)

        description = _optional_string(table_map.get("description"))
        columns = _normalize_columns(
            raw_columns=table_map.get("columns"),
            alias=alias,
            table_name=table_name,
            source_path=source_path,
        )

        table_item: dict[str, object] = {"name": table_name, "columns": columns}
        if description:
            table_item["description"] = description
        tables.append(table_item)

    return tables


def _normalize_columns(
    *,
    raw_columns: object,
    alias: str,
    table_name: str,
    source_path: Path,
) -> list[dict[str, str]]:
    """테이블 컬럼 목록을 정규화한다.

    규칙:
    - columns가 없으면 빈 리스트를 반환한다(=전체 허용 정책으로 상위 계층에서 해석 가능).
    """

    if raw_columns is None:
        return []
    if not isinstance(raw_columns, list):
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_COLUMNS",
            cause=f"alias={alias}, table={table_name}, columns는 리스트여야 합니다.",
            metadata={"source": str(source_path)},
        )
        raise BaseAppException("allowlist columns 형식이 올바르지 않습니다.", detail)

    columns: list[dict[str, str]] = []
    seen_column_names: set[str] = set()
    for column_index, raw_column in enumerate(raw_columns):
        column_name = ""
        description = ""
        if isinstance(raw_column, str):
            column_name = raw_column.strip()
        else:
            column_map = _to_string_key_dict(raw_column)
            if column_map is None:
                detail = ExceptionDetail(
                    code="TABLE_ALLOWLIST_INVALID_COLUMN",
                    cause=f"alias={alias}, table={table_name}, columns[{column_index}] 형식이 올바르지 않습니다.",
                    metadata={"source": str(source_path)},
                )
                raise BaseAppException(
                    "allowlist column 형식이 올바르지 않습니다.", detail
                )
            column_name = _required_string(
                column_map,
                key="name",
                parent=f"{alias}.{table_name}.columns[{column_index}]",
            )
            description = _optional_string(column_map.get("description"))

        if not column_name:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_INVALID_COLUMN",
                cause=f"alias={alias}, table={table_name}, columns[{column_index}] name이 비어 있습니다.",
                metadata={"source": str(source_path)},
            )
            raise BaseAppException("allowlist column 형식이 올바르지 않습니다.", detail)
        if column_name in seen_column_names:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_DUPLICATED_COLUMN",
                cause=f"alias={alias}, table={table_name}, column={column_name}",
                metadata={"source": str(source_path)},
            )
            raise BaseAppException("allowlist column 이름이 중복되었습니다.", detail)
        seen_column_names.add(column_name)

        column_item: dict[str, str] = {"name": column_name}
        if description:
            column_item["description"] = description
        columns.append(column_item)

    return columns


def _resolve_string(
    raw: Mapping[str, Any],
    *,
    value_key: str,
    env_key_key: str,
    required: bool,
) -> str:
    """직접값 또는 env 참조값을 문자열로 해석한다."""

    direct = _optional_string(raw.get(value_key))
    if direct:
        return direct

    env_key = _optional_string(raw.get(env_key_key))
    if env_key:
        env_value = _optional_string(os.getenv(env_key))
        if env_value:
            return env_value
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_ENV_NOT_FOUND",
            cause=f"env_key={env_key}",
            hint=f"{env_key_key}로 지정된 환경 변수 값을 설정하세요.",
        )
        raise BaseAppException("allowlist env 참조를 해석할 수 없습니다.", detail)

    if required:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_CONNECTION_INVALID",
            cause=f"{value_key} 또는 {env_key_key}가 필요합니다.",
        )
        raise BaseAppException("allowlist connection 설정이 올바르지 않습니다.", detail)
    return ""


def _resolve_int(
    raw: Mapping[str, Any],
    *,
    value_key: str,
    env_key_key: str,
    required: bool,
    default: int,
) -> int:
    """정수 직접값 또는 env 참조값을 해석한다."""

    direct_value = raw.get(value_key)
    if direct_value is not None and str(direct_value).strip():
        return _to_positive_int(direct_value, default=default, field_name=value_key)

    env_key = _optional_string(raw.get(env_key_key))
    if env_key:
        env_raw = _optional_string(os.getenv(env_key))
        if not env_raw:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_ENV_NOT_FOUND",
                cause=f"env_key={env_key}",
                hint=f"{env_key_key}로 지정된 환경 변수 값을 설정하세요.",
            )
            raise BaseAppException("allowlist env 참조를 해석할 수 없습니다.", detail)
        return _to_positive_int(env_raw, default=default, field_name=env_key)

    if required:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_CONNECTION_INVALID",
            cause=f"{value_key} 또는 {env_key_key}가 필요합니다.",
        )
        raise BaseAppException("allowlist connection 설정이 올바르지 않습니다.", detail)
    return default


def _required_string(raw: Mapping[str, Any], *, key: str, parent: str) -> str:
    """필수 문자열 값을 반환한다."""

    value = _optional_string(raw.get(key))
    if value:
        return value
    detail = ExceptionDetail(
        code="TABLE_ALLOWLIST_REQUIRED_FIELD_MISSING",
        cause=f"{parent}.{key} 값이 필요합니다.",
    )
    raise BaseAppException("allowlist 필수 값이 누락되었습니다.", detail)


def _optional_string(value: object) -> str:
    """선택 문자열을 정규화한다."""

    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def _to_positive_int(value: object, *, default: int, field_name: str) -> int:
    """양의 정수를 파싱한다."""

    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_NUMBER",
            cause=f"{field_name}는 정수여야 합니다: value={value!r}",
        )
        raise BaseAppException(
            "allowlist 숫자 값이 올바르지 않습니다.", detail
        ) from None
    if parsed <= 0:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_NUMBER",
            cause=f"{field_name}는 1 이상이어야 합니다: value={parsed}",
        )
        raise BaseAppException("allowlist 숫자 값이 올바르지 않습니다.", detail)
    return parsed if parsed > 0 else default


def _to_string_key_dict(value: object) -> dict[str, Any] | None:
    """임의 객체를 string-key dict로 변환한다."""

    if not isinstance(value, Mapping):
        return None
    return {str(key): item for key, item in value.items()}


__all__ = ["load_table_allowlist_config"]
