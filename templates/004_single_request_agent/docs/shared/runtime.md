# Shared Runtime

`src/single_request_agent/shared/runtime`의 보존 유틸을 코드 기준으로 정리한다.
이 모듈들은 현재 기본 `POST /agent` 런타임에는 포함되지 않으며, 필요 시 선택적으로 재사용하는 공용 유틸이다.

## 1. 현재 범위

복구 범위는 아래 3개로 제한한다.

| 유틸 | 역할 | 관련 스크립트 |
| --- | --- | --- |
| Queue | 작업 요청을 적재/소비하는 큐 컴포넌트 | `runtime/queue/*` |
| Worker | 큐를 소비해 핸들러를 실행하는 범용 워커 | `runtime/worker/*` |
| ThreadPool | 태스크 제출/종료를 관리하는 실행기 | `runtime/thread_pool/*` |

주의:

1. `buffer` 계층은 현재 복구 범위에 포함되지 않는다.
2. chat/session/SSE 전용 설명과 `ServiceExecutor` 연동 설명은 현재 구조에서 제외한다.
3. 기본 `/agent` 런타임은 이 모듈을 import하거나 조립하지 않는다.

## 2. 관련 스크립트

| 분류 | 파일 | 역할 |
| --- | --- | --- |
| 런타임 공개 API | `src/single_request_agent/shared/runtime/__init__.py` | Queue/Worker/ThreadPool 공개 |
| Queue 모델 | `src/single_request_agent/shared/runtime/queue/model.py` | `QueueConfig`, `QueueItem` |
| InMemory Queue | `src/single_request_agent/shared/runtime/queue/in_memory_queue.py` | 프로세스 내부 큐 |
| Redis Queue | `src/single_request_agent/shared/runtime/queue/redis_queue.py` | Redis 리스트 기반 큐 |
| Worker 모델 | `src/single_request_agent/shared/runtime/worker/model.py` | `WorkerConfig`, `WorkerState` |
| Worker 구현 | `src/single_request_agent/shared/runtime/worker/worker.py` | 큐 소비 워커 |
| ThreadPool 모델 | `src/single_request_agent/shared/runtime/thread_pool/model.py` | `ThreadPoolConfig`, `TaskRecord` |
| ThreadPool 구현 | `src/single_request_agent/shared/runtime/thread_pool/thread_pool.py` | 태스크 제출/종료 |

## 3. Queue 인터페이스

공통 메서드:

1. `put(payload, timeout)`
2. `get(timeout)`
3. `size()`
4. `close()`

### 3-1. InMemoryQueue 동작

1. `queue.Queue` 기반으로 동작한다.
2. 닫힌 큐에 `put()` 하면 `RuntimeError`를 발생시킨다.
3. `close()` 시 sentinel을 넣어 소비 루프 종료를 유도한다.
4. timeout이면 `None`을 반환한다.

### 3-2. RedisQueue 동작

1. `rpush`로 적재하고 `blpop`으로 소비한다.
2. `QueueItem`을 JSON 문자열로 직렬화한다.
3. `max_size`가 0보다 크면 busy wait로 용량을 제한한다.
4. decode 실패나 비동기 클라이언트 사용 시 명시적 예외를 발생시킨다.

## 4. Worker 인터페이스

핵심 요소:

1. 상태: `IDLE`, `RUNNING`, `STOPPED`, `ERROR`
2. 설정: `poll_timeout`, `max_retries`, `stop_on_error`
3. 등록: 데코레이터(`__call__`) 또는 직접 핸들러 지정
4. 수명주기: `start`, `stop`, context manager

동작 규칙:

1. 아이템 처리 실패 시 `max_retries`까지 재시도한다.
2. 재시도 초과 시 상태를 `ERROR`로 전환한다.
3. `stop_on_error=True`면 워커를 중지한다.

## 5. ThreadPool 인터페이스

핵심 요소:

1. 설정: `max_workers`, `thread_name_prefix`
2. 제출: `submit(fn, *args, **kwargs)`
3. 데코레이터: `task`
4. 종료: `shutdown(wait=True)`

동작 규칙:

1. `submit()` 시 필요하면 executor를 지연 생성한다.
2. 완료된 future는 내부 추적 목록에서 제거한다.
3. `shutdown()` 시 executor와 추적 목록을 정리한다.

## 6. 사용 위치 기준

현재 기준:

1. 기본 `/agent` 런타임 조립 경로는 `api/main.py`, `api/agent/services/runtime.py` 중심이다.
2. 위 경로는 `shared/runtime`를 import하지 않는다.
3. 따라서 이 모듈은 기본 런타임 기능이 아니라 선택적 공용 유틸로 본다.

## 7. 관련 문서

- `docs/shared/overview.md`
- `docs/setup/overview.md`
- `docs/setup/env.md`
