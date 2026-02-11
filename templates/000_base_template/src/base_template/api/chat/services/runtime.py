"""
목적: Chat API 런타임 조립 인스턴스를 제공한다.
설명: 그래프/서비스/큐/실행기를 모듈 레벨에서 조립해 라우터가 바로 사용할 인스턴스를 노출한다.
디자인 패턴: 모듈 조립 + 싱글턴
참조: src/base_template/core/chat/graphs/chat_graph.py
"""

from __future__ import annotations

import os
from typing import Any

from base_template.core.chat.graphs import chat_graph
from base_template.shared.chat import ChatHistoryRepository, ChatService, ServiceExecutor
from base_template.shared.chat.interface import StreamNodeConfig
from base_template.shared.logging import Logger, create_default_logger
from base_template.shared.runtime import InMemoryQueue, QueueConfig, RedisQueue


# 1) 로깅/저장소 의존성

# 서비스 실행 수명주기 로깅
service_logger: Logger = create_default_logger("ChatServiceExecutor")
# LLM 토큰 스트리밍 로깅
llm_logger: Logger = create_default_logger("ChatLLMExecutor")

# 세션/메시지 영속 저장소
history_repository = ChatHistoryRepository(logger=service_logger)

# 2) 그래프 실행 옵션

# LangGraph 체크포인터 주입값.
# None이면 ChatService.__init__에서 graph.compile(...)를 다시 호출하지 않는다.
# 이 경우 core/chat/graphs/chat_graph.py에서 BaseChatGraph 생성 시점에
# 이미 수행된 기본 compile(checkpointer=None) 결과를 그대로 사용한다.
checkpointer: Any | None = None
# 노드별로 API에 내보낼 스트림 이벤트 화이트리스트.
# 예: response 노드에서 token/assistant_message 이벤트만 통과.
stream_node: StreamNodeConfig = {
    "safeguard": ["safeguard_result"],
    "safeguard_route": ["safeguard_route", "safeguard_result"],
    "response": ["token", "assistant_message"],
    "blocked": ["assistant_message"],
}
# 요청 1건 기준 스트림 최대 실행 시간(초).
# ServiceExecutor가 시간 초과 시 error 이벤트로 종료한다.
timeout_seconds = float(os.getenv("CHAT_STREAM_TIMEOUT_SECONDS", "180.0"))

# 3) 큐 설정(memory/redis 공통)

# 큐 최대 적재 개수. 0이면 무제한(unbounded) 큐로 동작.
queue_max_size = int(os.getenv("CHAT_QUEUE_MAX_SIZE", "0"))
# 소비자(응답 스트림 루프)의 queue.get(...) 대기 시간(초).
# 값이 작을수록 응답성이 좋아지고, 너무 작으면 polling 오버헤드가 증가한다.
queue_poll_timeout = float(os.getenv("CHAT_QUEUE_POLL_TIMEOUT", "0.2"))
queue_config = QueueConfig(max_size=queue_max_size, default_timeout=queue_poll_timeout)

# 4) 큐 백엔드 선택

# CHAT_QUEUE_BACKEND="memory"(기본) | "redis"
# redis는 REDIS_URL이 유효할 때만 활성화, 그 외에는 자동으로 memory로 폴백된다.
queue_backend = os.getenv("CHAT_QUEUE_BACKEND", "memory").strip().lower()
redis_url = os.getenv("REDIS_URL", "").strip()
# Redis list key(큐 이름). 미설정 시 "chat-stream" 사용.
redis_queue_name = os.getenv("CHAT_REDIS_QUEUE_NAME", "chat-stream").strip() or "chat-stream"

if queue_backend == "redis" and redis_url:
    queue = RedisQueue(
        url=redis_url,
        name=redis_queue_name,
        config=queue_config,
        logger=service_logger,
    )
else:
    queue = InMemoryQueue(config=queue_config, logger=service_logger)

# 5) Chat 서비스/실행기 조립

# ChatService는 세션/메시지 저장 + 그래프 실행을 담당한다.
chat_service = ChatService(
    graph=chat_graph,
    checkpointer=checkpointer,
    stream_node=stream_node,
    repository=history_repository,
    logger=service_logger,
)

# ServiceExecutor는 ChatService.stream 결과를 queue를 통해 SSE로 중계한다.
service_executor = ServiceExecutor(
    service=chat_service,
    queue=queue,
    llm_logger=llm_logger,
    service_logger=service_logger,
    timeout_seconds=timeout_seconds,
)

# 6) FastAPI 주입/수명주기 함수
#
# 사용 위치:
# - get_chat_service():
#   - src/base_template/api/chat/routers/create_session.py
#   - src/base_template/api/chat/routers/list_sessions.py
#   - src/base_template/api/chat/routers/list_messages.py
#   - src/base_template/api/ui/services/__init__.py
# - get_service_executor():
#   - src/base_template/api/chat/routers/stream_session_message.py
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

    chat_service.close()


__all__ = [
    "chat_service",
    "service_executor",
    "get_chat_service",
    "get_service_executor",
    "shutdown_chat_api_service",
]
