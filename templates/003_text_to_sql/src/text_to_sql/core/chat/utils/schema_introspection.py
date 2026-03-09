"""
목적: Text-to-SQL allowlist 기반 스키마 introspection 유틸을 제공한다.
설명: target(alias/engine/connection/allowlist)을 기준으로 DB 메타데이터를 조회해 schema_snapshot을 생성한다.
디자인 패턴: 전략 분기 + 병렬 실행기
참조: src/text_to_sql/api/chat/services/runtime.py, src/text_to_sql/core/chat/nodes/schema_selection_prepare_node.py
"""

from __future__ import annotations

import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import Mapping
from typing import Any

from text_to_sql.shared.exceptions import BaseAppException, ExceptionDetail
from text_to_sql.shared.logging import Logger, create_default_logger

_DEFAULT_SAMPLE_ROW_LIMIT = 3


def introspect_allowlist_schema(
    *,
    table_allowlist: Mapping[str, Any],
    logger: Logger | None = None,
) -> dict[str, dict[str, object]]:
    """allowlist를 기준으로 DB introspection을 수행해 schema_snapshot을 만든다."""

    introspection_logger = logger or create_default_logger("SchemaIntrospection")
    raw_targets = table_allowlist.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID",
            cause="targets 목록이 비어 있거나 리스트가 아닙니다.",
        )
        raise BaseAppException("테이블 allowlist 형식이 올바르지 않습니다.", detail)

    normalized_targets: list[dict[str, Any]] = []
    for index, raw_target in enumerate(raw_targets):
        target = _to_string_key_dict(raw_target)
        if target is None:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_INVALID_TARGET",
                cause=f"targets[{index}]는 mapping이어야 합니다.",
            )
            raise BaseAppException(
                "테이블 allowlist target 형식이 올바르지 않습니다.", detail
            )
        normalized_targets.append(target)

    max_workers = _resolve_int_env("TEXT_TO_SQL_INTROSPECTION_MAX_WORKERS", default=4)
    worker_count = max(1, min(max_workers, len(normalized_targets)))
    snapshot: dict[str, dict[str, object]] = {}

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(_introspect_target_schema, target): str(
                target.get("alias") or ""
            ).strip()
            for target in normalized_targets
        }
        for future in as_completed(futures):
            alias = futures[future]
            try:
                partial = future.result()
            except BaseAppException:
                raise
            except Exception as error:  # noqa: BLE001 - 병렬 태스크 예외 래핑
                detail = ExceptionDetail(
                    code="SCHEMA_INTROSPECTION_FAILED",
                    cause=f"alias={alias}",
                    metadata={"error": repr(error)},
                )
                raise BaseAppException(
                    "스키마 introspection에 실패했습니다.", detail, error
                ) from error

            for table_key, table_spec in partial.items():
                if table_key in snapshot:
                    detail = ExceptionDetail(
                        code="TABLE_ALLOWLIST_DUPLICATED_TABLE",
                        cause=f"table_key={table_key}",
                    )
                    raise BaseAppException(
                        "allowlist table 이름이 중복되었습니다.", detail
                    )
                snapshot[table_key] = table_spec

    if not snapshot:
        detail = ExceptionDetail(
            code="SCHEMA_INTROSPECTION_EMPTY",
            cause="introspection 결과가 비어 있습니다.",
        )
        raise BaseAppException("스키마 introspection 결과가 비어 있습니다.", detail)

    introspection_logger.info(
        "schema introspection 완료: targets=%s, tables=%s"
        % (len(normalized_targets), len(snapshot))
    )
    return snapshot


def _introspect_target_schema(
    target: Mapping[str, Any],
) -> dict[str, dict[str, object]]:
    """target 단위 스키마 introspection을 수행한다."""

    alias = _required_string(target, "alias", "target")
    engine = _required_string(target, "engine", f"target({alias})").lower()

    raw_connection = _to_string_key_dict(target.get("connection"))
    if raw_connection is None:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_CONNECTION",
            cause=f"alias={alias}, connection이 mapping이 아닙니다.",
        )
        raise BaseAppException("allowlist connection 형식이 올바르지 않습니다.", detail)

    raw_allowlist = _to_string_key_dict(target.get("allowlist"))
    if raw_allowlist is None:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_ALLOWLIST",
            cause=f"alias={alias}, allowlist가 mapping이 아닙니다.",
        )
        raise BaseAppException("allowlist 형식이 올바르지 않습니다.", detail)

    table_specs = _normalize_allowlist_tables(
        alias=alias, raw_tables=raw_allowlist.get("tables")
    )

    if engine == "postgres":
        return _introspect_postgres(
            alias=alias, connection=raw_connection, tables=table_specs
        )
    if engine == "sqlite":
        return _introspect_sqlite(
            alias=alias, connection=raw_connection, tables=table_specs
        )
    if engine == "mongodb":
        return _introspect_mongodb(
            alias=alias, connection=raw_connection, tables=table_specs
        )

    detail = ExceptionDetail(
        code="TABLE_ALLOWLIST_ENGINE_UNSUPPORTED",
        cause=f"alias={alias}, engine={engine}",
    )
    raise BaseAppException("지원하지 않는 allowlist target engine입니다.", detail)


def _introspect_postgres(
    *,
    alias: str,
    connection: Mapping[str, Any],
    tables: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """PostgreSQL 대상 introspection을 수행한다."""

    import psycopg2

    schema = _optional_string(connection.get("schema")) or "public"
    table_names = sorted(tables.keys())
    if not table_names:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_TABLES",
            cause=f"alias={alias}, allowlist.tables가 비어 있습니다.",
        )
        raise BaseAppException("allowlist tables 형식이 올바르지 않습니다.", detail)

    connect_kwargs: dict[str, object] = {}
    dsn = _optional_string(connection.get("dsn"))
    if dsn:
        connect_kwargs["dsn"] = dsn
    else:
        connect_kwargs = {
            "host": _required_string(connection, "host", f"{alias}.connection"),
            "port": int(connection.get("port") or 5432),
            "user": _required_string(connection, "user", f"{alias}.connection"),
            "password": _optional_string(connection.get("password")) or None,
            "dbname": _required_string(connection, "database", f"{alias}.connection"),
        }

    placeholders = ", ".join(["%s"] * len(table_names))

    query_columns = (
        "SELECT table_name, column_name, data_type, udt_name "
        "FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name IN (" + placeholders + ") "
        "ORDER BY table_name, ordinal_position"
    )
    query_pks = (
        "SELECT tc.table_name, kcu.column_name "
        "FROM information_schema.table_constraints tc "
        "JOIN information_schema.key_column_usage kcu "
        "  ON tc.constraint_name = kcu.constraint_name "
        " AND tc.table_schema = kcu.table_schema "
        "WHERE tc.constraint_type = 'PRIMARY KEY' "
        "  AND tc.table_schema = %s "
        "  AND tc.table_name IN (" + placeholders + ") "
        "ORDER BY tc.table_name, kcu.ordinal_position"
    )
    query_fks = (
        "SELECT tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name "
        "FROM information_schema.table_constraints tc "
        "JOIN information_schema.key_column_usage kcu "
        "  ON tc.constraint_name = kcu.constraint_name "
        " AND tc.table_schema = kcu.table_schema "
        "JOIN information_schema.constraint_column_usage ccu "
        "  ON ccu.constraint_name = tc.constraint_name "
        "WHERE tc.constraint_type = 'FOREIGN KEY' "
        "  AND tc.table_schema = %s "
        "  AND tc.table_name IN (" + placeholders + ") "
        "  AND ccu.table_schema = %s"
    )

    columns_by_table: dict[str, list[str]] = {
        table_name: [] for table_name in table_names
    }
    column_types_by_table: dict[str, dict[str, str]] = {
        table_name: {} for table_name in table_names
    }
    pks_by_table: dict[str, list[str]] = {table_name: [] for table_name in table_names}
    fks_by_table: dict[str, list[dict[str, str]]] = {
        table_name: [] for table_name in table_names
    }

    connection_obj = None
    try:
        connection_obj = psycopg2.connect(**connect_kwargs)
        with connection_obj.cursor() as cursor:
            cursor.execute(query_columns, [schema, *table_names])
            for table_name, column_name, data_type, udt_name in cursor.fetchall():
                table_key = str(table_name).strip()
                column_key = str(column_name).strip()
                if table_key in columns_by_table and column_key:
                    columns_by_table[table_key].append(column_key)
                    column_types_by_table[table_key][column_key] = (
                        _normalize_postgres_type(
                            data_type=data_type,
                            udt_name=udt_name,
                        )
                    )

            cursor.execute(query_pks, [schema, *table_names])
            for table_name, pk_column in cursor.fetchall():
                table_key = str(table_name).strip()
                pk_key = str(pk_column).strip()
                if table_key in pks_by_table and pk_key:
                    pks_by_table[table_key].append(pk_key)

            cursor.execute(query_fks, [schema, *table_names, schema])
            for (
                table_name,
                column_name,
                ref_table_name,
                ref_column_name,
            ) in cursor.fetchall():
                table_key = str(table_name).strip()
                ref_table_key = str(ref_table_name).strip()
                if table_key not in fks_by_table or ref_table_key not in tables:
                    continue
                column_key = str(column_name).strip()
                ref_column_key = str(ref_column_name).strip()
                if not column_key or not ref_column_key:
                    continue
                fks_by_table[table_key].append(
                    {
                        "column": column_key,
                        "ref_table": f"{alias}.{ref_table_key}",
                        "ref_column": ref_column_key,
                    }
                )

            snapshot = _build_snapshot_from_introspection(
                alias=alias,
                schema_name=schema,
                tables=tables,
                columns_by_table=columns_by_table,
                column_types_by_table=column_types_by_table,
                pks_by_table=pks_by_table,
                fks_by_table=fks_by_table,
            )
            sample_limit = _resolve_int_env(
                "TEXT_TO_SQL_INTROSPECTION_SAMPLE_ROWS",
                default=_DEFAULT_SAMPLE_ROW_LIMIT,
            )
            _attach_postgres_sample_rows(
                cursor=cursor,
                schema=schema,
                snapshot=snapshot,
                sample_limit=sample_limit,
            )
            return snapshot
    except BaseAppException:
        raise
    except Exception as error:  # noqa: BLE001 - DB 드라이버 오류 래핑
        detail = ExceptionDetail(
            code="SCHEMA_INTROSPECTION_FAILED",
            cause=f"alias={alias}, engine=postgres",
            metadata={"error": repr(error)},
        )
        raise BaseAppException(
            "PostgreSQL introspection에 실패했습니다.", detail, error
        ) from error
    finally:
        if connection_obj is not None:
            connection_obj.close()


def _introspect_sqlite(
    *,
    alias: str,
    connection: Mapping[str, Any],
    tables: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """SQLite 대상 introspection을 수행한다."""

    db_path = _required_string(connection, "path", f"{alias}.connection")
    table_names = sorted(tables.keys())

    columns_by_table: dict[str, list[str]] = {
        table_name: [] for table_name in table_names
    }
    column_types_by_table: dict[str, dict[str, str]] = {
        table_name: {} for table_name in table_names
    }
    pks_by_table: dict[str, list[str]] = {table_name: [] for table_name in table_names}
    fks_by_table: dict[str, list[dict[str, str]]] = {
        table_name: [] for table_name in table_names
    }

    try:
        connection_obj = sqlite3.connect(db_path)
        try:
            cursor = connection_obj.cursor()
            for table_name in table_names:
                safe_name = table_name.replace('"', '""')
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                exists = cursor.fetchone()
                if not exists:
                    detail = ExceptionDetail(
                        code="SCHEMA_INTROSPECTION_TABLE_NOT_FOUND",
                        cause=f"alias={alias}, table={table_name}",
                    )
                    raise BaseAppException(
                        "allowlist에 정의한 테이블을 DB에서 찾을 수 없습니다.", detail
                    )

                cursor.execute(f'PRAGMA table_info("{safe_name}")')
                for row in cursor.fetchall():
                    column_name = str(row[1]).strip()
                    if not column_name:
                        continue
                    columns_by_table[table_name].append(column_name)
                    declared_type = str(row[2] or "").strip()
                    column_types_by_table[table_name][column_name] = (
                        declared_type or "unknown"
                    )
                    pk_order = int(row[5] or 0)
                    if pk_order > 0:
                        pks_by_table[table_name].append(column_name)

                cursor.execute(f'PRAGMA foreign_key_list("{safe_name}")')
                for row in cursor.fetchall():
                    ref_table = str(row[2]).strip()
                    if ref_table not in tables:
                        continue
                    from_column = str(row[3]).strip()
                    to_column = str(row[4]).strip()
                    if not from_column or not to_column:
                        continue
                    fks_by_table[table_name].append(
                        {
                            "column": from_column,
                            "ref_table": f"{alias}.{ref_table}",
                            "ref_column": to_column,
                        }
                    )

            snapshot = _build_snapshot_from_introspection(
                alias=alias,
                schema_name=None,
                tables=tables,
                columns_by_table=columns_by_table,
                column_types_by_table=column_types_by_table,
                pks_by_table=pks_by_table,
                fks_by_table=fks_by_table,
            )
            sample_limit = _resolve_int_env(
                "TEXT_TO_SQL_INTROSPECTION_SAMPLE_ROWS",
                default=_DEFAULT_SAMPLE_ROW_LIMIT,
            )
            _attach_sqlite_sample_rows(
                cursor=cursor,
                snapshot=snapshot,
                sample_limit=sample_limit,
            )
            return snapshot
        finally:
            connection_obj.close()
    except BaseAppException:
        raise
    except Exception as error:  # noqa: BLE001 - sqlite 오류 래핑
        detail = ExceptionDetail(
            code="SCHEMA_INTROSPECTION_FAILED",
            cause=f"alias={alias}, engine=sqlite",
            metadata={"error": repr(error)},
        )
        raise BaseAppException(
            "SQLite introspection에 실패했습니다.", detail, error
        ) from error


def _introspect_mongodb(
    *,
    alias: str,
    connection: Mapping[str, Any],
    tables: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """MongoDB 대상 introspection을 수행한다.

    MongoDB는 스키마리스이므로 컬럼 구조는 allowlist 정의를 기준으로 유지하고,
    컬렉션 존재 여부만 검증한다.
    """

    from pymongo import MongoClient

    database = _required_string(connection, "database", f"{alias}.connection")
    dsn = _optional_string(connection.get("dsn"))
    auth_source = _optional_string(connection.get("auth_source"))

    client = None
    try:
        if dsn:
            if auth_source:
                client = MongoClient(dsn, authSource=auth_source)
            else:
                client = MongoClient(dsn)
        else:
            host = _required_string(connection, "host", f"{alias}.connection")
            port = int(connection.get("port") or 27017)
            user = _optional_string(connection.get("user"))
            password = _optional_string(connection.get("password"))
            auth = ""
            if user and password:
                auth = f"{user}:{password}@"
            elif user:
                auth = f"{user}@"
            uri = f"mongodb://{auth}{host}:{port}"
            if auth_source and auth:
                client = MongoClient(uri, authSource=auth_source)
            else:
                client = MongoClient(uri)

        db = client[database]
        existing = set(db.list_collection_names())
        sample_limit = _resolve_int_env(
            "TEXT_TO_SQL_INTROSPECTION_SAMPLE_ROWS",
            default=_DEFAULT_SAMPLE_ROW_LIMIT,
        )

        snapshot: dict[str, dict[str, object]] = {}
        for table_name, table_spec in sorted(tables.items()):
            if table_name not in existing:
                detail = ExceptionDetail(
                    code="SCHEMA_INTROSPECTION_TABLE_NOT_FOUND",
                    cause=f"alias={alias}, collection={table_name}",
                )
                raise BaseAppException(
                    "allowlist에 정의한 컬렉션을 DB에서 찾을 수 없습니다.", detail
                )

            allow_columns = table_spec.get("allow_columns")
            selected_columns = (
                [str(column).strip() for column in allow_columns if str(column).strip()]
                if isinstance(allow_columns, list)
                else []
            )
            column_descriptions = table_spec.get("column_descriptions")
            description = str(table_spec.get("description") or "").strip()

            collection = db[table_name]
            projection: dict[str, int] | None = None
            if selected_columns:
                projection = {str(column): 1 for column in selected_columns}
                if "_id" not in projection:
                    projection["_id"] = 0

            docs_cursor = collection.find({}, projection).limit(sample_limit)
            raw_docs = list(docs_cursor)
            sample_rows = [
                _sanitize_sample_mapping(doc)
                for doc in raw_docs
                if isinstance(doc, Mapping)
            ]

            column_types: dict[str, str] = {}
            if selected_columns:
                for column_name in selected_columns:
                    column_types[column_name] = _infer_mongo_field_type(
                        docs=raw_docs,
                        field_name=column_name,
                    )
            else:
                inferred_fields: dict[str, str] = {}
                for doc in raw_docs:
                    if not isinstance(doc, Mapping):
                        continue
                    for key, value in doc.items():
                        field = str(key)
                        if field in inferred_fields:
                            continue
                        inferred_fields[field] = _infer_python_type_name(value)
                column_types = dict(
                    sorted(inferred_fields.items(), key=lambda item: item[0])
                )

            table_key = f"{alias}.{table_name}"
            snapshot[table_key] = {
                "target_alias": alias,
                "table_name": table_name,
                "schema_name": "",
                "qualified_table_name": table_name,
                "description": description,
                "columns": selected_columns,
                "column_descriptions": (
                    dict(column_descriptions)
                    if isinstance(column_descriptions, dict)
                    else {}
                ),
                "column_types": column_types,
                "sample_rows": sample_rows,
                "primary_keys": ["_id"],
                "foreign_keys": [],
            }
        return snapshot
    except BaseAppException:
        raise
    except Exception as error:  # noqa: BLE001 - mongo 오류 래핑
        detail = ExceptionDetail(
            code="SCHEMA_INTROSPECTION_FAILED",
            cause=f"alias={alias}, engine=mongodb",
            metadata={"error": repr(error)},
        )
        raise BaseAppException(
            "MongoDB introspection에 실패했습니다.", detail, error
        ) from error
    finally:
        if client is not None:
            client.close()


def _build_snapshot_from_introspection(
    *,
    alias: str,
    schema_name: str | None,
    tables: dict[str, dict[str, object]],
    columns_by_table: Mapping[str, list[str]],
    column_types_by_table: Mapping[str, dict[str, str]],
    pks_by_table: Mapping[str, list[str]],
    fks_by_table: Mapping[str, list[dict[str, str]]],
) -> dict[str, dict[str, object]]:
    """introspection 결과와 allowlist를 결합해 schema_snapshot을 생성한다."""

    snapshot: dict[str, dict[str, object]] = {}
    for table_name, table_spec in sorted(tables.items()):
        actual_columns = columns_by_table.get(table_name, [])
        if not actual_columns:
            detail = ExceptionDetail(
                code="SCHEMA_INTROSPECTION_TABLE_NOT_FOUND",
                cause=f"alias={alias}, table={table_name}",
            )
            raise BaseAppException(
                "allowlist에 정의한 테이블을 DB에서 찾을 수 없습니다.", detail
            )

        allow_columns = table_spec.get("allow_columns")
        actual_lookup = {
            str(name).lower(): str(name) for name in actual_columns if str(name).strip()
        }
        raw_column_descriptions = table_spec.get("column_descriptions")
        column_descriptions_lookup = (
            {
                str(key): str(value)
                for key, value in raw_column_descriptions.items()
                if str(key).strip() and str(value).strip()
            }
            if isinstance(raw_column_descriptions, Mapping)
            else {}
        )
        selected_columns: list[str]
        selected_column_descriptions: dict[str, str] = {}
        if isinstance(allow_columns, list) and allow_columns:
            actual_set = {name.lower() for name in actual_columns}
            missing = [
                name for name in allow_columns if str(name).lower() not in actual_set
            ]
            if missing:
                detail = ExceptionDetail(
                    code="SCHEMA_INTROSPECTION_COLUMN_NOT_FOUND",
                    cause=f"alias={alias}, table={table_name}, missing={missing}",
                )
                raise BaseAppException(
                    "allowlist 컬럼이 DB 스키마와 일치하지 않습니다.", detail
                )
            selected_columns = []
            seen_selected: set[str] = set()
            for allow_name in allow_columns:
                allow_name_text = str(allow_name)
                actual_name = actual_lookup.get(
                    allow_name_text.lower(), allow_name_text
                )
                normalized_actual = actual_name.lower()
                if normalized_actual in seen_selected:
                    continue
                seen_selected.add(normalized_actual)
                selected_columns.append(actual_name)
                description_text = column_descriptions_lookup.get(allow_name_text)
                if description_text:
                    selected_column_descriptions[actual_name] = description_text
        else:
            selected_columns = list(actual_columns)
            for column_name in selected_columns:
                description_text = column_descriptions_lookup.get(column_name)
                if description_text:
                    selected_column_descriptions[column_name] = description_text

        table_types = column_types_by_table.get(table_name, {})
        type_lookup = {
            str(col_name).lower(): str(col_type or "unknown")
            for col_name, col_type in table_types.items()
            if str(col_name).strip()
        }
        selected_column_types: dict[str, str] = {}
        for column_name in selected_columns:
            normalized = column_name.lower()
            selected_column_types[column_name] = type_lookup.get(normalized, "unknown")

        selected_set = {name.lower() for name in selected_columns}
        raw_fks = fks_by_table.get(table_name, [])
        filtered_fks: list[dict[str, str]] = []
        dedup_fk: set[tuple[str, str, str]] = set()
        for fk in raw_fks:
            source_column = str(fk.get("column") or "").strip()
            ref_table = str(fk.get("ref_table") or "").strip()
            ref_column = str(fk.get("ref_column") or "").strip()
            if not source_column or not ref_table or not ref_column:
                continue
            if source_column.lower() not in selected_set:
                continue
            signature = (source_column.lower(), ref_table.lower(), ref_column.lower())
            if signature in dedup_fk:
                continue
            dedup_fk.add(signature)
            filtered_fks.append(
                {
                    "column": source_column,
                    "ref_table": ref_table,
                    "ref_column": ref_column,
                }
            )

        column_descriptions = table_spec.get("column_descriptions")
        description = str(table_spec.get("description") or "").strip()
        normalized_schema_name = str(schema_name or "").strip()
        qualified_table_name = (
            f"{normalized_schema_name}.{table_name}"
            if normalized_schema_name
            else table_name
        )
        quoted_qualified_table_name = (
            f'{_quote_identifier(normalized_schema_name)}.{_quote_identifier(table_name)}'
            if normalized_schema_name
            else _quote_identifier(table_name)
        )
        quoted_columns = {
            column_name: _quote_identifier(column_name) for column_name in selected_columns
        }

        table_key = f"{alias}.{table_name}"
        snapshot[table_key] = {
            "target_alias": alias,
            "table_name": table_name,
            "schema_name": normalized_schema_name,
            "qualified_table_name": qualified_table_name,
            "quoted_qualified_table_name": quoted_qualified_table_name,
            "description": description,
            "columns": selected_columns,
            "quoted_columns": quoted_columns,
            "column_descriptions": selected_column_descriptions,
            "column_types": selected_column_types,
            "sample_rows": [],
            "primary_keys": [
                str(item)
                for item in pks_by_table.get(table_name, [])
                if str(item).strip()
            ],
            "foreign_keys": filtered_fks,
        }

    return snapshot


def _attach_postgres_sample_rows(
    *,
    cursor: Any,
    schema: str,
    snapshot: dict[str, dict[str, object]],
    sample_limit: int,
) -> None:
    """PostgreSQL snapshot에 sample_rows를 채운다."""

    for table_spec in snapshot.values():
        if not isinstance(table_spec, dict):
            continue
        table_name = str(table_spec.get("table_name") or "").strip()
        raw_columns = table_spec.get("columns")
        selected_columns = (
            [str(item).strip() for item in raw_columns if str(item).strip()]
            if isinstance(raw_columns, list)
            else []
        )
        if not table_name or not selected_columns:
            table_spec["sample_rows"] = []
            continue

        safe_schema = _quote_identifier(schema)
        safe_table = _quote_identifier(table_name)
        select_clause = ", ".join(
            _quote_identifier(column) for column in selected_columns
        )
        query = f"SELECT {select_clause} FROM {safe_schema}.{safe_table} LIMIT %s"
        cursor.execute(query, (sample_limit,))
        rows = cursor.fetchall()

        sample_rows: list[dict[str, object]] = []
        for row in rows:
            values = tuple(row) if isinstance(row, (list, tuple)) else ()
            record: dict[str, object] = {}
            for index, column_name in enumerate(selected_columns):
                value = values[index] if index < len(values) else None
                record[column_name] = _sanitize_sample_value(value)
            sample_rows.append(record)
        table_spec["sample_rows"] = sample_rows


def _attach_sqlite_sample_rows(
    *,
    cursor: sqlite3.Cursor,
    snapshot: dict[str, dict[str, object]],
    sample_limit: int,
) -> None:
    """SQLite snapshot에 sample_rows를 채운다."""

    for table_spec in snapshot.values():
        if not isinstance(table_spec, dict):
            continue
        table_name = str(table_spec.get("table_name") or "").strip()
        raw_columns = table_spec.get("columns")
        selected_columns = (
            [str(item).strip() for item in raw_columns if str(item).strip()]
            if isinstance(raw_columns, list)
            else []
        )
        if not table_name or not selected_columns:
            table_spec["sample_rows"] = []
            continue

        safe_table = table_name.replace('"', '""')
        select_clause = ", ".join(
            f'"{column.replace('"', '""')}"' for column in selected_columns
        )
        query = f'SELECT {select_clause} FROM "{safe_table}" LIMIT ?'
        cursor.execute(query, (sample_limit,))
        rows = cursor.fetchall()

        sample_rows: list[dict[str, object]] = []
        for row in rows:
            values = tuple(row) if isinstance(row, (list, tuple)) else ()
            record: dict[str, object] = {}
            for index, column_name in enumerate(selected_columns):
                value = values[index] if index < len(values) else None
                record[column_name] = _sanitize_sample_value(value)
            sample_rows.append(record)
        table_spec["sample_rows"] = sample_rows


def _normalize_postgres_type(*, data_type: object, udt_name: object) -> str:
    normalized_data_type = _optional_string(data_type).lower()
    normalized_udt_name = _optional_string(udt_name).lower()
    if normalized_data_type == "array" and normalized_udt_name.startswith("_"):
        return f"array<{normalized_udt_name[1:]}>"
    if normalized_data_type:
        return normalized_data_type
    if normalized_udt_name:
        return normalized_udt_name
    return "unknown"


def _quote_identifier(identifier: str) -> str:
    safe = str(identifier).replace('"', '""')
    return f'"{safe}"'


def _sanitize_sample_mapping(raw: object) -> dict[str, object]:
    if not isinstance(raw, Mapping):
        return {}
    return {str(key): _sanitize_sample_value(value) for key, value in raw.items()}


def _sanitize_sample_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Mapping):
        return _sanitize_sample_mapping(value)
    if isinstance(value, list):
        return [_sanitize_sample_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_sample_value(item) for item in value]
    return str(value)


def _infer_mongo_field_type(*, docs: list[Any], field_name: str) -> str:
    for doc in docs:
        if not isinstance(doc, Mapping):
            continue
        if field_name not in doc:
            continue
        return _infer_python_type_name(doc.get(field_name))
    return "unknown"


def _infer_python_type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, bytes):
        return "bytes"
    if isinstance(value, list):
        return "list"
    if isinstance(value, tuple):
        return "tuple"
    if isinstance(value, Mapping):
        return "object"
    return type(value).__name__


def _normalize_allowlist_tables(
    *, alias: str, raw_tables: object
) -> dict[str, dict[str, object]]:
    """allowlist tables를 table_name 기준 dict로 정규화한다."""

    if not isinstance(raw_tables, list) or not raw_tables:
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID_TABLES",
            cause=f"alias={alias}, allowlist.tables가 비어 있습니다.",
        )
        raise BaseAppException("allowlist tables 형식이 올바르지 않습니다.", detail)

    tables: dict[str, dict[str, object]] = {}
    for index, raw_table in enumerate(raw_tables):
        table_map = _to_string_key_dict(raw_table)
        if table_map is None:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_INVALID_TABLE",
                cause=f"alias={alias}, tables[{index}]는 mapping이어야 합니다.",
            )
            raise BaseAppException("allowlist table 형식이 올바르지 않습니다.", detail)

        table_name = _required_string(table_map, "name", f"{alias}.tables[{index}]")
        if table_name in tables:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_DUPLICATED_TABLE",
                cause=f"alias={alias}, table={table_name}",
            )
            raise BaseAppException("allowlist table 이름이 중복되었습니다.", detail)

        description = _optional_string(table_map.get("description"))
        column_descriptions: dict[str, str] = {}
        allow_columns: list[str] = []
        raw_columns = table_map.get("columns")
        if isinstance(raw_columns, list):
            seen_columns: set[str] = set()
            for column_index, raw_column in enumerate(raw_columns):
                column_name = ""
                if isinstance(raw_column, str):
                    column_name = raw_column.strip()
                else:
                    column_map = _to_string_key_dict(raw_column)
                    if column_map is None:
                        detail = ExceptionDetail(
                            code="TABLE_ALLOWLIST_INVALID_COLUMN",
                            cause=f"alias={alias}, table={table_name}, columns[{column_index}] 형식이 올바르지 않습니다.",
                        )
                        raise BaseAppException(
                            "allowlist column 형식이 올바르지 않습니다.", detail
                        )
                    column_name = _required_string(
                        column_map,
                        "name",
                        f"{alias}.{table_name}.columns[{column_index}]",
                    )
                    description_text = _optional_string(column_map.get("description"))
                    if description_text:
                        column_descriptions[column_name] = description_text
                if not column_name:
                    continue
                normalized = column_name.lower()
                if normalized in seen_columns:
                    continue
                seen_columns.add(normalized)
                allow_columns.append(column_name)

        tables[table_name] = {
            "description": description,
            "allow_columns": allow_columns,
            "column_descriptions": column_descriptions,
        }
    return tables


def _resolve_int_env(env_key: str, *, default: int) -> int:
    raw = _optional_string(os.getenv(env_key))
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value <= 0:
        return default
    return value


def _required_string(raw: Mapping[str, Any], key: str, parent: str) -> str:
    value = _optional_string(raw.get(key))
    if value:
        return value
    detail = ExceptionDetail(
        code="TABLE_ALLOWLIST_REQUIRED_FIELD_MISSING",
        cause=f"{parent}.{key} 값이 필요합니다.",
    )
    raise BaseAppException("allowlist 필수 값이 누락되었습니다.", detail)


def _optional_string(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def _to_string_key_dict(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return {str(key): item for key, item in value.items()}


__all__ = ["introspect_allowlist_schema"]
