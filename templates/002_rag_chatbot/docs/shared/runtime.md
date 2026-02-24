# Shared Runtime 가이드

이 문서는 `src/rag_chatbot/shared/runtime`의 Queue, EventBuffer, Worker, ThreadPool 구성요소를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| Queue | 작업 요청을 적재/소비하는 큐 컴포넌트 | `runtime/queue/*` |
| EventBuffer | request 단위 이벤트를 임시 저장/전달하는 버퍼 | `runtime/buffer/*` |
| QueueItem | 큐에 저장되는 단위 레코드 | `queue/model.py` |
| StreamEventItem | 이벤트 버퍼에 저장되는 단위 이벤트 | `buffer/model.py` |
| Worker | 큐를 소비해 핸들러를 실행하는 범용 워커 | `worker/worker.py` |
| ThreadPool | 비동기 작업 제출/종료를 관리하는 실행기 | `thread_pool/thread_pool.py` |
| TTL | 버퍼 키 또는 버킷을 자동 정리하는 만료 시간 | `EventBufferConfig` |

## 2. 관련 스크립트

| 분류 | 파일 | 역할 |
| --- | --- | --- |
| 런타임 공개 API | `src/rag_chatbot/shared/runtime/__init__.py` | Queue/Buffer/Worker/ThreadPool 공개 |
| Queue 모델 | `src/rag_chatbot/shared/runtime/queue/model.py` | `QueueConfig`, `QueueItem` |
| InMemory Queue | `src/rag_chatbot/shared/runtime/queue/in_memory_queue.py` | 프로세스 내부 큐 |
| Redis Queue | `src/rag_chatbot/shared/runtime/queue/redis_queue.py` | Redis 리스트 기반 큐 |
| Buffer 모델 | `src/rag_chatbot/shared/runtime/buffer/model.py` | `EventBufferConfig`, `StreamEventItem` |
| InMemory Buffer | `src/rag_chatbot/shared/runtime/buffer/in_memory_buffer.py` | 요청 버킷 기반 이벤트 버퍼 |
| Redis Buffer | `src/rag_chatbot/shared/runtime/buffer/redis_buffer.py` | Redis 리스트 기반 이벤트 버퍼 |
| Worker 모델 | `src/rag_chatbot/shared/runtime/worker/model.py` | `WorkerConfig`, `WorkerState` |
| Worker 구현 | `src/rag_chatbot/shared/runtime/worker/worker.py` | 큐 소비 워커 |
| ThreadPool 모델 | `src/rag_chatbot/shared/runtime/thread_pool/model.py` | `ThreadPoolConfig`, `TaskRecord` |
| ThreadPool 구현 | `src/rag_chatbot/shared/runtime/thread_pool/thread_pool.py` | 태스크 제출/종료 |

연동 스크립트:

1. `src/rag_chatbot/api/chat/services/runtime.py`
2. `src/rag_chatbot/shared/chat/services/service_executor.py`

## 3. 현재 Chat 경로에서의 사용 방식

현재 기본 조립:

```text
InMemoryQueue + InMemoryEventBuffer + ServiceExecutor
```

의미:

1. Chat 요청 실행은 `ServiceExecutor` 내부 워커 스레드가 처리한다.
2. `shared/runtime/worker`, `thread_pool`은 공용 유틸로 제공되며 Chat 기본 경로에서 직접 사용하지 않는다.

## 4. Queue 인터페이스

공통 메서드:

1. `put(payload, timeout)`
2. `get(timeout)`
3. `size()`
4. `close()`

## 4-1. InMemoryQueue 동작

1. `queue.Queue` 기반으로 동작한다.
2. 닫힌 큐에 put하면 `RuntimeError`를 발생시킨다.
3. close 시 sentinel을 넣어 소비 루프 종료를 유도한다.
4. timeout이면 `None`을 반환한다.

## 4-2. RedisQueue 동작

1. `rpush`로 적재, `blpop`으로 소비한다.
2. `QueueItem`을 JSON 문자열로 직렬화한다.
3. `max_size`가 0보다 크면 busy-wait로 용량을 제한한다.
4. `redis` 패키지가 없으면 `RuntimeError`를 발생시킨다.

## 5. EventBuffer 인터페이스

공통 메서드:

1. `push(session_id, request_id, event)`
2. `pop(session_id, request_id, timeout)`
3. `cleanup(session_id, request_id)`
4. `size(session_id, request_id)`

## 5-1. InMemoryEventBuffer 동작

1. 버킷 키 형식은 `session_id:request_id`다.
2. `in_memory_ttl_seconds`와 `in_memory_gc_interval_seconds`로 버킷 GC를 수행한다.
3. invalid event 입력이면 `ValueError`를 발생시킨다.
4. bucket이 없고 timeout이 있으면 해당 시간 sleep 후 `None`을 반환한다.

## 5-2. RedisEventBuffer 동작

1. 키 형식은 `<prefix>:<session_id>:<request_id>`다.
2. `push` 시 `redis_ttl_seconds`가 설정돼 있으면 expire를 설정한다.
3. `blpop` 기반으로 이벤트를 소비한다.
4. decode 실패 시 `ValueError`를 발생시킨다.

## 6. Worker 인터페이스

핵심 요소:

1. 상태: `IDLE`, `RUNNING`, `STOPPED`, `ERROR`
2. 설정: `poll_timeout`, `max_retries`, `stop_on_error`
3. 등록: 데코레이터(`__call__`) 또는 직접 핸들러 지정
4. 수명주기: `start`, `stop`, context manager

동작 규칙:

1. 아이템 처리 실패 시 `max_retries`까지 재시도한다.
2. 재시도 초과 시 상태를 ERROR로 전환한다.
3. `stop_on_error=True`면 워커를 중지한다.

## 7. ThreadPool 인터페이스

핵심 요소:

1. 설정: `max_workers`, `thread_name_prefix`
2. 제출: `submit(fn, *args, **kwargs)`
3. 데코레이터: `task`
4. 종료: `shutdown(wait=True)`

동작 규칙:

1. `submit` 시 자동으로 executor를 생성한다.
2. 완료된 future는 내부 목록에서 제거한다.
3. shutdown 시 executor와 추적 목록을 정리한다.

## 8. 변경 작업 절차

## 8-1. Queue를 Redis로 전환

1. `api/chat/services/runtime.py`에서 `InMemoryQueue`를 `RedisQueue`로 교체한다.
2. Redis URL/큐 이름/timeout/max_size를 환경 변수로 주입한다.
3. 직렬화 불가능 payload가 없는지 점검한다.

## 8-2. EventBuffer를 Redis로 전환

1. `InMemoryEventBuffer`를 `RedisEventBuffer`로 교체한다.
2. `redis_key_prefix`, `redis_ttl_seconds`를 운영값으로 설정한다.
3. stream 종료 시 `cleanup` 호출이 유지되는지 확인한다.

## 8-3. Worker 도입

1. 큐 소비 작업을 함수 단위로 분리한다.
2. `WorkerConfig`로 재시도/정지 정책을 설정한다.
3. 실패 시 ERROR 상태 전이와 로그 기록을 확인한다.

## 8-4. ThreadPool 도입

1. 병렬화 대상 작업을 `submit` 단위로 분리한다.
2. 작업 완료 콜백과 예외 처리 전략을 정의한다.
3. 종료 시 `shutdown`이 누락되지 않도록 수명주기를 고정한다.

## 9. 트러블슈팅

| 증상 | 원인 후보 | 확인 스크립트 | 조치 |
| --- | --- | --- | --- |
| 큐가 가득 차 put 실패 | max_size 제한 도달 | `queue/redis_queue.py`, `queue/in_memory_queue.py` | max_size/소비 속도 조정 |
| 이벤트가 누적되어 메모리 증가 | cleanup 누락 또는 TTL 과대 | `buffer/in_memory_buffer.py`, `service_executor.py` | cleanup 호출과 TTL/GC 조정 |
| Redis 연결 실패 | URL 오류 또는 패키지 미설치 | `queue/redis_queue.py`, `buffer/redis_buffer.py` | 연결 문자열/의존성 확인 |
| Worker가 바로 ERROR로 전이 | handler 예외 + 재시도 초과 | `worker/worker.py` | handler 예외 처리 보강 |
| ThreadPool 작업이 누락됨 | shutdown 타이밍 문제 | `thread_pool/thread_pool.py` | 수명주기 관리 방식 점검 |

## 10. 소스 매칭 점검 항목

1. Queue/Buffer/Worker/ThreadPool 메서드 설명이 코드 시그니처와 일치하는가
2. 상태값/기본값이 모델 정의와 일치하는가
3. 키 형식/TTL 설명이 Redis/InMemory 구현과 일치하는가
4. 문서 경로가 실제 `src/rag_chatbot/shared/runtime` 구조와 일치하는가

## 11. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat.md`
- `docs/api/chat.md`
