"""
목적: Chat API 런타임 조립 인스턴스를 제공한다.
설명: 그래프/서비스/큐/실행기를 모듈 레벨에서 조립해 라우터가 바로 사용할 인스턴스를 노출한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/base_template/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

import os

from base_template.core.chat.graphs import chat_graph
from base_template.shared.chat import ChatHistoryRepository, ChatService, ServiceExecutor
from base_template.shared.logging import Logger, create_default_logger
from base_template.shared.runtime import (
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

# 세션/메시지 영속 저장소
# 현재는 ChatHistoryRepository 기본값(db_client=None)을 사용하므로 SQLite 경로(CHAT_DB_PATH)에 저장된다.
history_repository = ChatHistoryRepository(logger=service_logger)

# PostgreSQL로 저장소를 사용 하는 경우
#   from base_template.integrations.db import DBClient
#   from base_template.integrations.db.engines.postgres import PostgresEngine
#   from base_template.shared.chat import ChatHistoryRepository

#   # PostgreSQL 엔진 생성
#   postgres_engine = PostgresEngine(
#       dsn=(os.getenv("POSTGRES_DSN") or "").strip() or None,
#       host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
#       port=int(os.getenv("POSTGRES_PORT", "5432")),
#       user=os.getenv("POSTGRES_USER", "postgres"),
#       password=(os.getenv("POSTGRES_PW") or "").strip() or None,
#       database=os.getenv("POSTGRES_DATABASE", "playground"),
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
timeout_seconds = float(os.getenv("CHAT_STREAM_TIMEOUT_SECONDS", "180.0"))
persist_retry_limit = int(os.getenv("CHAT_PERSIST_RETRY_LIMIT", "2"))
persist_retry_delay_seconds = float(os.getenv("CHAT_PERSIST_RETRY_DELAY_SECONDS", "0.5"))

# 3) 작업 큐(JobQueue) 설정(memory/redis 공통)
# 현재 런타임은 분기 없이 InMemoryQueue를 고정 사용한다.
# Redis JobQueue 전환은 추후 조립 코드에서 별도 개발한다.

# 큐 최대 적재 개수. 0이면 무제한(unbounded) 큐로 동작.
queue_max_size = int(os.getenv("CHAT_JOB_QUEUE_MAX_SIZE", os.getenv("CHAT_QUEUE_MAX_SIZE", "0")))

# 소비자(백엔드 워커)의 queue.get(...) 대기 시간(초).
# 값이 작을수록 응답성이 좋아지고, 너무 작으면 polling 오버헤드가 증가한다.
queue_poll_timeout = float(
    os.getenv("CHAT_JOB_QUEUE_POLL_TIMEOUT", os.getenv("CHAT_QUEUE_POLL_TIMEOUT", "0.2"))
)
job_queue_config = QueueConfig(max_size=queue_max_size, default_timeout=queue_poll_timeout)

# 작업 큐(JobQueue) 인스턴스
job_queue = InMemoryQueue(config=job_queue_config, logger=service_logger)

# RedisQueue로 작업 큐를 사용 하는 경우
#   from base_template.shared.runtime import RedisQueue

#   redis_url = (os.getenv("REDIS_URL") or "").strip()
#   redis_queue_name = (
#       os.getenv("CHAT_REDIS_JOB_QUEUE_NAME", os.getenv("CHAT_REDIS_QUEUE_NAME", "chat-job")).strip()
#       or "chat-job"
#   )

#   # RedisQueue 주입 방식으로 JobQueue 생성
#   job_queue = RedisQueue(
#       url=redis_url,
#       name=redis_queue_name,
#       config=job_queue_config,
#       logger=service_logger,
#   )

# 4) 이벤트 버퍼(EventBuffer) 설정
# 현재 런타임은 분기 없이 InMemoryEventBuffer를 고정 사용한다.
# Redis EventBuffer 전환은 추후 조립 코드에서 별도 개발한다.

event_buffer_max_size = int(os.getenv("CHAT_EVENT_BUFFER_MAX_SIZE", "0"))
event_buffer_poll_timeout = float(os.getenv("CHAT_EVENT_BUFFER_POLL_TIMEOUT", "0.2"))
event_buffer_gc_interval_seconds = float(os.getenv("CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS", "30.0"))
event_buffer_ttl_seconds = int(os.getenv("CHAT_EVENT_BUFFER_TTL_SECONDS", "600"))
event_buffer_key_prefix = (
    os.getenv("CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX", "chat:stream").strip() or "chat:stream"
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
)

# 6) FastAPI 주입/수명주기 함수
#
# 사용 위치:
# - get_chat_service():
#   - src/base_template/api/chat/routers/get_chat_session.py
#   - src/base_template/api/ui/services/__init__.py
# - get_service_executor():
#   - src/base_template/api/chat/routers/create_chat.py
#   - src/base_template/api/chat/routers/stream_chat_events.py
# - shutdown_chat_api_service():
#   - src/base_template/api/main.py (lifespan 종료 구간)
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

    service_executor.shutdown()
    chat_service.close()


__all__ = [
    "chat_service",
    "service_executor",
    "get_chat_service",
    "get_service_executor",
    "shutdown_chat_api_service",
]
