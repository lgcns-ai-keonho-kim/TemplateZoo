# 런타임 동시성 명세

이 문서는 `src/base_template/shared/runtime`의 Queue/Worker/ThreadPool 동작 규칙을 정의한다.

## 구성 요소

| 컴포넌트 | 파일 | 역할 |
| --- | --- | --- |
| InMemory Queue | `shared/runtime/queue/in_memory_queue.py` | 프로세스 내부 큐, 블로킹 `put/get`, 종료 센티널 |
| Redis Queue | `shared/runtime/queue/redis_queue.py` | Redis 리스트 기반 큐, `rpush/blpop` |
| Worker | `shared/runtime/worker/worker.py` | 큐 소비 루프, 핸들러 실행, 재시도/중단 정책 |
| ThreadPool | `shared/runtime/thread_pool/thread_pool.py` | 비동기 실행 위임, Future 관리 |

## Import 규칙

애플리케이션 계층(`api/*`)에서는 런타임 하위 모듈을 직접 import하지 않는다.

- 사용: `from base_template.shared.runtime import InMemoryQueue, QueueConfig, QueueItem, Worker, WorkerConfig, ThreadPool, ThreadPoolConfig`
- 금지: `from base_template.shared.runtime.queue ...`, `from base_template.shared.runtime.worker ...`, `from base_template.shared.runtime.thread_pool ...`

하위 모듈(`shared/runtime/*`) 내부 구현 파일에서는 필요한 경우에만 구체 모듈 간 import를 허용한다.

## Queue 규칙

### InMemoryQueue

- `put(payload)`는 `QueueItem`을 생성해 큐에 적재한다.
- `get(timeout)`은 타임아웃 시 `None`을 반환한다.
- `close()`는 센티널을 넣어 소비 루프 종료를 유도한다.

### RedisQueue

- `put(payload)`는 JSON 직렬화 후 Redis 리스트에 저장한다.
- `get(timeout)`은 `blpop` 결과를 `QueueItem`으로 복원한다.
- `QueueConfig.max_size`는 폴링 기반 제한으로 동작한다.

## Worker 규칙

1. `@worker` 데코레이터로 핸들러를 등록한다.
2. `start()` 호출 후 백그라운드 스레드가 `queue.get()`를 반복 호출한다.
3. 핸들러 예외 발생 시 `max_retries` 범위 내 재시도한다.
4. 재시도 초과 시 `WorkerState.ERROR`로 전이한다.
5. `stop_on_error=True`이면 오류 발생 시 루프를 중단한다.

현재 `Worker`는 `InMemoryQueue` 타입을 직접 받는다.

## ThreadPool 규칙

1. `submit(fn, *args, **kwargs)`는 `Future`를 반환한다.
2. `@pool.task` 데코레이터는 함수 호출을 Future 반환 함수로 감싼다.
3. `shutdown(wait=True)`는 실행기 종료를 보장한다.
4. `with ThreadPool()` 구문은 생성/종료를 자동화한다.

## Chat에서의 사용 방식

`api/chat/services/task_manager.py`는 다음 구조로 사용한다.

```text
InMemoryQueue -> Worker -> ThreadPool -> ChatRuntime.process_enqueued_turn
```

추가 규칙:

- 세션 단위 락으로 같은 `session_id` 태스크를 직렬 실행한다.
- 스트림 버퍼는 `rpush/lpop` 패턴으로 토큰 전달을 구현한다.
- 큐 포화 시 `CHAT_QUEUE_FULL` 오류를 반환해 백프레셔를 적용한다.
- 완료/실패 태스크는 TTL 기반으로 정리되고, 최대 보관 개수를 넘으면 오래된 결과부터 제거한다.

## TaskManager 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_TASK_MAX_WORKERS` | `max(4, cpu*4)` | 백그라운드 태스크 실행 스레드 수 |
| `CHAT_TASK_QUEUE_MAX_SIZE` | `1000` | 큐 최대 크기 (`0`은 무제한) |
| `CHAT_TASK_STREAM_MAX_CHUNKS` | `4096` | 태스크별 스트림 버퍼 청크 상한 (`0`은 무제한) |
| `CHAT_TASK_RESULT_TTL_SECONDS` | `1800` | 완료/실패 태스크 보관 시간(초) |
| `CHAT_TASK_MAX_STORED` | `10000` | 메모리 내 태스크 최대 보관 개수 |
| `CHAT_TASK_CLEANUP_INTERVAL_SECONDS` | `30` | 태스크 정리 주기(초) |

## 의존성

```text
api/chat/services/task_manager
  -> shared/runtime (퍼사드)
     -> shared/runtime/queue
     -> shared/runtime/worker
     -> shared/runtime/thread_pool
```
