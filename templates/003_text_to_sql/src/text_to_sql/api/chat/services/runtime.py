"""
목적: Chat API 런타임 조립 인스턴스를 제공한다.
설명: 그래프/서비스/큐/실행기를 모듈 레벨에서 조립해 라우터가 바로 사용할 인스턴스를 노출한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/text_to_sql/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from text_to_sql.core.chat.graphs import chat_graph
from text_to_sql.core.chat.utils.schema_introspection import introspect_allowlist_schema
from text_to_sql.integrations.db import DBClient, QueryTargetRegistry
from text_to_sql.integrations.db.base.models import CollectionSchema, ColumnSpec
from text_to_sql.integrations.db.engines.mongodb import MongoDBEngine
from text_to_sql.integrations.db.engines.postgres import PostgresEngine
from text_to_sql.integrations.db.engines.sqlite import SQLiteEngine
from text_to_sql.shared.chat import ChatHistoryRepository, ChatService, ServiceExecutor
from text_to_sql.shared.chat.runtime import (
    InMemoryAssistantContextStore,
    RedisAssistantContextStore,
    close_assistant_context_store,
    clear_query_target_registry,
    set_assistant_context_store,
    set_query_target_registry,
)
from text_to_sql.shared.exceptions import BaseAppException, ExceptionDetail
from text_to_sql.shared.logging import Logger, create_default_logger
from text_to_sql.shared.runtime import (
    EventBufferConfig,
    InMemoryEventBuffer,
    InMemoryQueue,
    QueueConfig,
)


# 1) 로깅/저장소 의존성

# 서비스 실행 수명주기 로깅
service_logger: Logger = create_default_logger("ChatServiceExecutor")
# LLM 토큰 스트리밍 로깅
llm_logger: Logger = create_default_logger("ChatLLMExecutor")
_runtime_logger: Logger = create_default_logger("TextToSQLRuntime")

# 세션/메시지 영속 저장소
# 현재는 ChatHistoryRepository 기본값(db_client=None)을 사용하므로 SQLite 경로(CHAT_DB_PATH)에 저장된다.
history_repository = ChatHistoryRepository(logger=service_logger)

# PostgreSQL로 저장소를 사용 하는 경우
#   from text_to_sql.integrations.db import DBClient
#   from text_to_sql.integrations.db.engines.postgres import PostgresEngine
#   from text_to_sql.shared.chat import ChatHistoryRepository

#   # PostgreSQL 엔진 생성
#   postgres_engine = PostgresEngine(
#       dsn=(os.getenv("POSTGRES_DSN") or "").strip() or None,
#       host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
#       port=int(os.getenv("POSTGRES_PORT", "5432")),
#       user=os.getenv("POSTGRES_USER", "postgres"),
#       password=(os.getenv("POSTGRES_PW") or "").strip() or None,
#       # database 값은 table_allowlist.yaml target 설정에서 주입
#       database="x1",
#       logger=service_logger,
#   )

#   # DBClient 주입 방식으로 Chat 저장소 생성
#   history_repository = ChatHistoryRepository(
#       db_client=DBClient(postgres_engine),
#       logger=service_logger,
#   )


# 2) 그래프 실행 옵션

# checkpointer/stream_node 정책은 core/chat/graphs/chat_graph.py에서 단일 관리한다.
# 요청 1건 기준 스트림 최대 실행 시간(초).
# ServiceExecutor가 시간 초과 시 error 이벤트로 종료한다.
timeout_seconds = float(os.getenv("CHAT_STREAM_TIMEOUT_SECONDS", "120.0"))
persist_retry_limit = int(os.getenv("CHAT_PERSIST_RETRY_LIMIT", "2"))
persist_retry_delay_seconds = float(
    os.getenv("CHAT_PERSIST_RETRY_DELAY_SECONDS", "0.5")
)

# 3) 작업 큐(JobQueue) 설정(memory/redis 공통)
# 현재 런타임은 분기 없이 InMemoryQueue를 고정 사용한다.
# Redis JobQueue 전환은 추후 조립 코드에서 별도 개발한다.

# 큐 최대 적재 개수. 0이면 무제한(unbounded) 큐로 동작.
queue_max_size = int(
    os.getenv("CHAT_JOB_QUEUE_MAX_SIZE", os.getenv("CHAT_QUEUE_MAX_SIZE", "0"))
)

# 소비자(백엔드 워커)의 queue.get(...) 대기 시간(초).
# 값이 작을수록 응답성이 좋아지고, 너무 작으면 polling 오버헤드가 증가한다.
queue_poll_timeout = float(
    os.getenv(
        "CHAT_JOB_QUEUE_POLL_TIMEOUT", os.getenv("CHAT_QUEUE_POLL_TIMEOUT", "0.2")
    )
)
job_queue_config = QueueConfig(
    max_size=queue_max_size, default_timeout=queue_poll_timeout
)

# 작업 큐(JobQueue) 인스턴스
job_queue = InMemoryQueue(config=job_queue_config, logger=service_logger)

# RedisQueue로 작업 큐를 사용 하는 경우
#   from text_to_sql.shared.runtime import RedisQueue

#   redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
#   redis_port = int(os.getenv("REDIS_PORT", "6379"))
#   redis_db = int(os.getenv("REDIS_DB", "0"))
#   redis_password = (os.getenv("REDIS_PW") or "").strip() or None
#   redis_queue_name = (
#       os.getenv("CHAT_REDIS_JOB_QUEUE_NAME", os.getenv("CHAT_REDIS_QUEUE_NAME", "chat-job")).strip()
#       or "chat-job"
#   )

#   # RedisQueue 주입 방식으로 JobQueue 생성
#   job_queue = RedisQueue(
#       url=f"redis://{redis_host}:{redis_port}/{redis_db}",
#       name=redis_queue_name,
#       config=job_queue_config,
#       logger=service_logger,
#   )

# 4) 이벤트 버퍼(EventBuffer) 설정
# 현재 런타임은 분기 없이 InMemoryEventBuffer를 고정 사용한다.
# Redis EventBuffer 전환은 추후 조립 코드에서 별도 개발한다.

event_buffer_max_size = int(os.getenv("CHAT_EVENT_BUFFER_MAX_SIZE", "0"))
event_buffer_poll_timeout = float(os.getenv("CHAT_EVENT_BUFFER_POLL_TIMEOUT", "0.2"))
event_buffer_gc_interval_seconds = float(
    os.getenv("CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS", "30.0")
)
event_buffer_ttl_seconds = int(os.getenv("CHAT_EVENT_BUFFER_TTL_SECONDS", "600"))
event_buffer_key_prefix = (
    os.getenv("CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX", "chat:stream").strip()
    or "chat:stream"
)

event_buffer_config = EventBufferConfig(
    max_size=event_buffer_max_size,
    default_timeout=event_buffer_poll_timeout,
    redis_key_prefix=event_buffer_key_prefix,
    redis_ttl_seconds=event_buffer_ttl_seconds,
    in_memory_ttl_seconds=event_buffer_ttl_seconds,
    in_memory_gc_interval_seconds=event_buffer_gc_interval_seconds,
)

# 이벤트 버퍼(EventBuffer) 인스턴스
event_buffer = InMemoryEventBuffer(config=event_buffer_config, logger=service_logger)

# 5) assistant 컨텍스트 캐시 설정
#
# 목적:
# - done 이후 DB persist 비동기 구간에서도 직전 assistant 응답을 즉시 재사용하기 위해
#   세션별 마지막 assistant 컨텍스트를 별도 캐시에 저장한다.
# - backend 선택은 runtime.py에서 명시적으로 주입한다.
#
# 설계 포인트:
# - 본 캐시는 "세션별 마지막 assistant 응답 1건"만 다룬다.
# - JobQueue/EventBuffer와는 역할이 다르며, 키 충돌을 피하기 위해 prefix를 분리한다.
# - in_memory는 단일 프로세스 개발/로컬 테스트 용도, redis는 멀티 인스턴스 운영 용도다.
# - ttl/max_sessions는 메모리 상한 제어(만료 + LRU 축출)에 사용된다.

# 캐시 백엔드 선택: in_memory | redis
assistant_context_backend = (
    os.getenv("CHAT_ASSISTANT_CONTEXT_BACKEND", "in_memory").strip().lower()
    or "in_memory"
)
# TTL(초): 마지막 접근 시각 기준 만료
assistant_context_ttl_seconds = max(
    1, int(os.getenv("CHAT_ASSISTANT_CONTEXT_TTL_SECONDS", "1800"))
)
# 세션 최대 개수: 초과 시 오래된 세션부터 LRU 축출
assistant_context_max_sessions = max(
    1, int(os.getenv("CHAT_ASSISTANT_CONTEXT_MAX_SESSIONS", "2000"))
)
# Redis key prefix: 세션별 컨텍스트 레코드 저장 키
assistant_context_redis_key_prefix = (
    os.getenv("CHAT_ASSISTANT_CONTEXT_REDIS_KEY_PREFIX", "chat:assistant_ctx").strip()
    or "chat:assistant_ctx"
)
# Redis ZSET 키: LRU 정리를 위한 인덱스 키
assistant_context_redis_lru_index_key = (
    os.getenv(
        "CHAT_ASSISTANT_CONTEXT_REDIS_LRU_INDEX_KEY", "chat:assistant_ctx:lru"
    ).strip()
    or "chat:assistant_ctx:lru"
)


def _load_redis_connection_params() -> tuple[str, int, int, str | None]:
    """환경변수에서 Redis 연결 파라미터를 로드한다."""

    # 정책: Redis는 URL 대신 REDIS_HOST/PORT/DB/PW만 사용한다.
    # 이유: 배포 환경별 설정 포맷을 단순화하고, .env 표준 키와 일치시키기 위함.
    host = str(os.getenv("REDIS_HOST", "127.0.0.1") or "").strip()
    port_raw = str(os.getenv("REDIS_PORT", "6379") or "").strip()
    db_raw = str(os.getenv("REDIS_DB", "0") or "").strip()
    password_raw = str(os.getenv("REDIS_PW") or "").strip()
    if not host:
        raise RuntimeError("REDIS_HOST 환경 변수가 필요합니다.")
    try:
        port = int(port_raw)
    except ValueError as error:
        raise RuntimeError("REDIS_PORT는 정수여야 합니다.") from error
    if port <= 0:
        raise RuntimeError("REDIS_PORT는 1 이상의 정수여야 합니다.")
    try:
        db = int(db_raw)
    except ValueError as error:
        raise RuntimeError("REDIS_DB는 정수여야 합니다.") from error
    if db < 0:
        raise RuntimeError("REDIS_DB는 0 이상의 정수여야 합니다.")
    password = password_raw or None
    return host, port, db, password


def _build_assistant_context_store():
    """assistant 컨텍스트 캐시 저장소를 생성한다."""

    # in_memory: 프로세스 수명 동안만 유지되는 경량 캐시
    if assistant_context_backend == "in_memory":
        return InMemoryAssistantContextStore(
            ttl_seconds=assistant_context_ttl_seconds,
            max_sessions=assistant_context_max_sessions,
            logger=service_logger,
        )

    # redis: 멀티 프로세스/멀티 인스턴스에서도 동일 세션 컨텍스트 공유 가능
    if assistant_context_backend == "redis":
        redis_host, redis_port, redis_db, redis_password = (
            _load_redis_connection_params()
        )
        store = RedisAssistantContextStore(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            ttl_seconds=assistant_context_ttl_seconds,
            max_sessions=assistant_context_max_sessions,
            key_prefix=assistant_context_redis_key_prefix,
            lru_index_key=assistant_context_redis_lru_index_key,
            logger=service_logger,
        )
        # 정책: redis backend는 startup 시 fail-fast
        # - 연결 불가 상태를 런타임 지연 에러로 미루지 않고, 기동 단계에서 즉시 중단한다.
        store.ping()
        return store

    raise RuntimeError(
        "CHAT_ASSISTANT_CONTEXT_BACKEND는 in_memory 또는 redis만 지원합니다."
    )


# 런타임 전역 store 등록:
# - context_strategy_prepare 등 그래프 노드에서 동일 인스턴스를 참조한다.
assistant_context_store = _build_assistant_context_store()
set_assistant_context_store(assistant_context_store)

# 5) Chat 서비스/실행기 조립

# ChatService는 세션/메시지 저장 + 그래프 실행을 담당한다.
chat_service = ChatService(
    graph=chat_graph,
    repository=history_repository,
    logger=service_logger,
)

# ServiceExecutor는 JobQueue를 소비해 EventBuffer에 이벤트를 적재한다.
service_executor = ServiceExecutor(
    service=chat_service,
    job_queue=job_queue,
    event_buffer=event_buffer,
    llm_logger=llm_logger,
    service_logger=service_logger,
    timeout_seconds=timeout_seconds,
    persist_retry_limit=persist_retry_limit,
    persist_retry_delay_seconds=persist_retry_delay_seconds,
    assistant_context_store=assistant_context_store,
)

# 5-1) Text-to-SQL 런타임 컨텍스트

_text_to_sql_runtime_context: dict[str, object] = {
    "table_allowlist": {},
    "schema_snapshot": {},
    "targets": {},
    "query_target_registry": None,
}


def initialize_text_to_sql_runtime(
    *, table_allowlist: Mapping[str, Any]
) -> dict[str, object]:
    """startup에서 allowlist 기반 Text-to-SQL 런타임 컨텍스트를 초기화한다."""

    clear_query_target_registry()
    allowlist_map = {str(key): value for key, value in table_allowlist.items()}
    targets = _build_targets(allowlist_map)
    schema_snapshot = introspect_allowlist_schema(
        table_allowlist=allowlist_map,
        logger=_runtime_logger,
    )
    query_target_registry = _build_query_target_registry(
        targets=targets,
        schema_snapshot=schema_snapshot,
    )

    _text_to_sql_runtime_context["table_allowlist"] = allowlist_map
    _text_to_sql_runtime_context["schema_snapshot"] = schema_snapshot
    _text_to_sql_runtime_context["targets"] = targets
    _text_to_sql_runtime_context["query_target_registry"] = query_target_registry
    set_query_target_registry(query_target_registry)

    if hasattr(chat_graph, "set_static_input"):
        chat_graph.set_static_input(
            {
                "schema_snapshot": schema_snapshot,
            }
        )

    _runtime_logger.info(
        "text_to_sql runtime 초기화 완료: targets=%s, tables=%s, default_target=%s"
        % (
            len(targets),
            len(schema_snapshot),
            query_target_registry.default_alias,
        )
    )

    return get_text_to_sql_runtime_context()


def get_text_to_sql_runtime_context() -> dict[str, object]:
    """현재 Text-to-SQL 런타임 컨텍스트 스냅샷을 반환한다."""

    query_target_registry = _text_to_sql_runtime_context.get("query_target_registry")
    default_target_alias = (
        query_target_registry.default_alias
        if isinstance(query_target_registry, QueryTargetRegistry)
        else ""
    )
    target_aliases = (
        query_target_registry.aliases()
        if isinstance(query_target_registry, QueryTargetRegistry)
        else []
    )
    return {
        "table_allowlist": _text_to_sql_runtime_context.get("table_allowlist", {}),
        "schema_snapshot": _text_to_sql_runtime_context.get("schema_snapshot", {}),
        "targets": _text_to_sql_runtime_context.get("targets", {}),
        "default_target_alias": default_target_alias,
        "target_aliases": target_aliases,
    }


def _build_targets(table_allowlist: dict[str, Any]) -> dict[str, dict[str, object]]:
    raw_targets = table_allowlist.get("targets")
    if not isinstance(raw_targets, list):
        detail = ExceptionDetail(
            code="TABLE_ALLOWLIST_INVALID",
            cause="targets는 리스트여야 합니다.",
        )
        raise BaseAppException("테이블 allowlist 형식이 올바르지 않습니다.", detail)

    targets: dict[str, dict[str, object]] = {}
    for index, raw_target in enumerate(raw_targets):
        if not isinstance(raw_target, Mapping):
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_INVALID_TARGET",
                cause=f"targets[{index}]는 mapping이어야 합니다.",
            )
            raise BaseAppException(
                "테이블 allowlist target 형식이 올바르지 않습니다.", detail
            )
        target = {str(key): value for key, value in raw_target.items()}
        alias = str(target.get("alias") or "").strip()
        engine = str(target.get("engine") or "").strip()
        raw_connection = target.get("connection")
        if not alias or not engine or not isinstance(raw_connection, Mapping):
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_INVALID_TARGET",
                cause=f"targets[{index}]의 alias/engine/connection을 확인하세요.",
            )
            raise BaseAppException(
                "테이블 allowlist target 형식이 올바르지 않습니다.", detail
            )
        targets[alias] = {
            "alias": alias,
            "engine": engine,
            "connection": {str(key): value for key, value in raw_connection.items()},
        }
    return targets


def _build_query_target_registry(
    *,
    targets: dict[str, dict[str, object]],
    schema_snapshot: dict[str, dict[str, object]],
) -> QueryTargetRegistry:
    """target 정의를 기반으로 QueryTargetRegistry를 구성한다."""

    registry = QueryTargetRegistry()
    for index, alias in enumerate(sorted(targets.keys())):
        target = targets[alias]
        engine_name = str(target.get("engine") or "").strip().lower()
        connection = target.get("connection")
        if not isinstance(connection, Mapping):
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_INVALID_CONNECTION",
                cause=f"alias={alias}, connection이 mapping이 아닙니다.",
            )
            raise BaseAppException(
                "allowlist connection 형식이 올바르지 않습니다.", detail
            )

        try:
            client = _create_query_target_client(
                alias=alias,
                engine_name=engine_name,
                connection={str(key): value for key, value in connection.items()},
            )
            _register_target_schemas(
                client=client,
                target_alias=alias,
                schema_snapshot=schema_snapshot,
            )
            registry.register(
                alias=alias,
                client=client,
                engine=engine_name,
                is_default=index == 0,
            )
        except BaseAppException:
            registry.close_all()
            raise
        except Exception as error:  # noqa: BLE001 - 연결/등록 오류를 도메인 예외로 래핑
            registry.close_all()
            detail = ExceptionDetail(
                code="SQL_RUNTIME_TARGET_INIT_FAILED",
                cause=f"alias={alias}, engine={engine_name}",
                metadata={"error": repr(error)},
            )
            raise BaseAppException(
                "Text-to-SQL target 초기화에 실패했습니다.", detail, error
            ) from error

    return registry


def _create_query_target_client(
    *,
    alias: str,
    engine_name: str,
    connection: dict[str, object],
) -> DBClient:
    """target 1건의 DBClient를 생성한다."""

    if engine_name == "postgres":
        dsn = str(connection.get("dsn") or "").strip() or None
        if dsn:
            engine = PostgresEngine(dsn=dsn, logger=_runtime_logger)
        else:
            host = str(connection.get("host") or "").strip()
            user = str(connection.get("user") or "").strip()
            database = str(connection.get("database") or "").strip()
            if not host or not user or not database:
                detail = ExceptionDetail(
                    code="TABLE_ALLOWLIST_CONNECTION_INVALID",
                    cause=f"alias={alias}, host/user/database가 필요합니다.",
                )
                raise BaseAppException(
                    "PostgreSQL connection 설정이 올바르지 않습니다.", detail
                )
            port = _to_int(connection.get("port"), default=5432)
            password = str(connection.get("password") or "").strip() or None
            engine = PostgresEngine(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                logger=_runtime_logger,
            )
        return DBClient(engine)

    if engine_name == "sqlite":
        path = str(connection.get("path") or "").strip()
        if not path:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_CONNECTION_INVALID",
                cause=f"alias={alias}, path가 필요합니다.",
            )
            raise BaseAppException(
                "SQLite connection 설정이 올바르지 않습니다.", detail
            )
        return DBClient(SQLiteEngine(database_path=path, logger=_runtime_logger))

    if engine_name == "mongodb":
        dsn = str(connection.get("dsn") or "").strip() or None
        database = str(connection.get("database") or "").strip()
        if not database:
            detail = ExceptionDetail(
                code="TABLE_ALLOWLIST_CONNECTION_INVALID",
                cause=f"alias={alias}, database가 필요합니다.",
            )
            raise BaseAppException(
                "MongoDB connection 설정이 올바르지 않습니다.", detail
            )

        if dsn:
            engine = MongoDBEngine(
                uri=dsn,
                database=database,
                auth_source=str(connection.get("auth_source") or "").strip() or None,
                logger=_runtime_logger,
            )
        else:
            host = str(connection.get("host") or "").strip()
            if not host:
                detail = ExceptionDetail(
                    code="TABLE_ALLOWLIST_CONNECTION_INVALID",
                    cause=f"alias={alias}, host가 필요합니다.",
                )
                raise BaseAppException(
                    "MongoDB connection 설정이 올바르지 않습니다.", detail
                )
            port = _to_int(connection.get("port"), default=27017)
            user = str(connection.get("user") or "").strip() or None
            password = str(connection.get("password") or "").strip() or None
            auth_source = str(connection.get("auth_source") or "").strip() or None
            engine = MongoDBEngine(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                auth_source=auth_source,
                logger=_runtime_logger,
            )
        return DBClient(engine)

    detail = ExceptionDetail(
        code="TABLE_ALLOWLIST_ENGINE_UNSUPPORTED",
        cause=f"alias={alias}, engine={engine_name}",
    )
    raise BaseAppException("지원하지 않는 target engine입니다.", detail)


def _register_target_schemas(
    *,
    client: DBClient,
    target_alias: str,
    schema_snapshot: dict[str, dict[str, object]],
) -> None:
    """introspection 스냅샷 기반 CollectionSchema를 DBClient에 등록한다."""

    registered_count = 0
    for table_key, table_spec in sorted(schema_snapshot.items()):
        if not isinstance(table_spec, Mapping):
            continue
        table_alias = (
            str(table_spec.get("target_alias") or "").strip()
            or table_key.split(".", 1)[0]
        )
        if table_alias != target_alias:
            continue

        table_name = str(table_spec.get("table_name") or "").strip()
        if not table_name:
            continue
        qualified_table_name = str(table_spec.get("qualified_table_name") or "").strip()
        collection_name = qualified_table_name or table_name
        raw_columns = table_spec.get("columns")
        columns: list[str] = []
        if isinstance(raw_columns, list):
            seen: set[str] = set()
            for item in raw_columns:
                column_name = str(item).strip()
                if not column_name:
                    continue
                normalized = column_name.lower()
                if normalized in seen:
                    continue
                seen.add(normalized)
                columns.append(column_name)

        raw_primary_keys = table_spec.get("primary_keys")
        primary_keys: list[str] = []
        if isinstance(raw_primary_keys, list):
            seen_pk: set[str] = set()
            for item in raw_primary_keys:
                pk_name = str(item).strip()
                if not pk_name:
                    continue
                normalized_pk = pk_name.lower()
                if normalized_pk in seen_pk:
                    continue
                seen_pk.add(normalized_pk)
                primary_keys.append(pk_name)

        primary_key = ""
        if primary_keys:
            primary_key = primary_keys[0]
        elif columns:
            primary_key = columns[0]
        else:
            primary_key = "doc_id"

        pk_set = {item.lower() for item in primary_keys}
        column_specs = [
            ColumnSpec(name=column, is_primary=column.lower() in pk_set)
            for column in columns
        ]
        schema = CollectionSchema(
            name=collection_name,
            primary_key=primary_key,
            payload_field=None,
            vector_field=None,
            columns=column_specs,
            metadata={
                "target_alias": target_alias,
                "schema_key": table_key,
                "table_name": table_name,
                "description": str(table_spec.get("description") or "").strip(),
            },
        )
        client.register_schema(schema)
        registered_count += 1

    if registered_count <= 0:
        detail = ExceptionDetail(
            code="SQL_RUNTIME_SCHEMA_REGISTER_EMPTY",
            cause=f"alias={target_alias}, 등록할 테이블을 찾지 못했습니다.",
        )
        raise BaseAppException("target 스키마 등록 대상이 비어 있습니다.", detail)


def _to_int(value: object, *, default: int) -> int:
    """정수값을 안전하게 파싱한다."""

    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default


# 6) FastAPI 주입/수명주기 함수
#
# 사용 위치:
# - get_chat_service():
#   - src/text_to_sql/api/chat/routers/get_chat_session.py
#   - src/text_to_sql/api/ui/services/__init__.py
# - get_service_executor():
#   - src/text_to_sql/api/chat/routers/create_chat.py
#   - src/text_to_sql/api/chat/routers/stream_chat_events.py
# - shutdown_chat_api_service():
#   - src/text_to_sql/api/main.py (lifespan 종료 구간)
#
# 의도:
# - 라우터에서는 FastAPI Depends로 아래 함수만 호출해 의존성을 가져오고,
# - 조립/생성 로직은 runtime.py 내부에만 고정한다.


def get_chat_service() -> ChatService:
    """FastAPI Depends 경유로 ChatService 싱글턴을 반환한다."""

    return chat_service


def get_service_executor() -> ServiceExecutor:
    """FastAPI Depends 경유로 ServiceExecutor 싱글턴을 반환한다."""

    return service_executor


def shutdown_chat_api_service() -> None:
    """앱 종료 시 ChatService가 소유한 저장소/연결 리소스를 정리한다."""

    try:
        service_executor.shutdown()
    finally:
        try:
            chat_service.close()
        finally:
            query_target_registry = _text_to_sql_runtime_context.get(
                "query_target_registry"
            )
            if isinstance(query_target_registry, QueryTargetRegistry):
                query_target_registry.close_all()
            clear_query_target_registry()
            close_assistant_context_store()


__all__ = [
    "chat_service",
    "service_executor",
    "get_chat_service",
    "get_service_executor",
    "initialize_text_to_sql_runtime",
    "get_text_to_sql_runtime_context",
    "shutdown_chat_api_service",
]
