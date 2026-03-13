# Shared Runtime

## 패키지 구성

- `queue`: `InMemoryQueue`, `RedisQueue`, `QueueConfig`, `QueueItem`
- `buffer`: `InMemoryEventBuffer`, `RedisEventBuffer`, `EventBufferConfig`, `StreamEventItem`
- `worker`: `Worker`
- `thread_pool`: `ThreadPool`

## 기본 Chat API 조립

- 실제 Chat API 런타임은 `InMemoryQueue`와 `InMemoryEventBuffer`를 고정 사용한다.
- `Worker`와 `ThreadPool`은 패키지 구성 요소이지만 기본 Chat API 조립 경로에는 직접 쓰이지 않는다.
- Redis 구현은 모듈로 존재하지만 `src/rag_chatbot/api/chat/services/runtime.py`에서 선택하지 않으면 활성화되지 않는다.

## 이벤트 계약

- 내부 이벤트 타입: `start`, `token`, `references`, `done`, `error`
- 버퍼 키: `session_id + request_id`
- InMemory 버퍼: TTL과 GC 주기 사용
- Redis 버퍼: key prefix와 TTL 사용

## 기본 설정 소스

- 큐 설정: `CHAT_JOB_QUEUE_MAX_SIZE`, `CHAT_QUEUE_MAX_SIZE`, `CHAT_JOB_QUEUE_POLL_TIMEOUT`, `CHAT_QUEUE_POLL_TIMEOUT`
- 버퍼 설정: `CHAT_EVENT_BUFFER_MAX_SIZE`, `CHAT_EVENT_BUFFER_POLL_TIMEOUT`, `CHAT_EVENT_BUFFER_TTL_SECONDS`, `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS`, `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX`
- 타임아웃: `CHAT_STREAM_TIMEOUT_SECONDS`
