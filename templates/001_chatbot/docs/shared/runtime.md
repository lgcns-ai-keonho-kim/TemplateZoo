# Shared Runtime 레퍼런스

`src/chatbot/shared/runtime`은 큐, 이벤트 버퍼, 워커, 스레드풀을 제공하는 공용 런타임 유틸 계층이다.

## 1. 구성 요소

| 영역 | 대표 타입 | 구현 |
| --- | --- | --- |
| Queue | `QueueConfig`, `QueueItem` | `InMemoryQueue`, `RedisQueue` |
| Buffer | `EventBufferConfig`, `StreamEventItem` | `InMemoryEventBuffer`, `RedisEventBuffer` |
| Worker | `WorkerConfig`, `WorkerState` | `Worker` |
| ThreadPool | `ThreadPoolConfig`, `TaskRecord` | `ThreadPool` |

현재 기본 채팅 경로에서 직접 쓰는 조합:

```text
InMemoryQueue + InMemoryEventBuffer + ServiceExecutor
```

## 2. Queue

### 2-1. `InMemoryQueue`

1. `queue.Queue` 기반 구현이다.
2. `put()`은 `QueueItem`으로 감싸 저장한다.
3. `close()`는 센티널을 넣어 종료를 유도한다.

### 2-2. `RedisQueue`

1. Redis 리스트를 사용한다.
2. 저장은 `RPUSH`, 소비는 `BLPOP`으로 동작한다.
3. `redis` 패키지가 없으면 연결 시점에 `RuntimeError`를 낸다.
4. `max_size > 0`일 때는 크기 제한을 polling으로 보장한다.

## 3. Event Buffer

### 3-1. `InMemoryEventBuffer`

1. 버킷 키는 `session_id:request_id` 형식이다.
2. 요청 단위 큐를 만들고 `push/pop/cleanup`을 제공한다.
3. TTL과 GC 주기 기준으로 만료 버킷을 정리한다.

### 3-2. `RedisEventBuffer`

1. 버킷 키는 `<prefix>:<session_id>:<request_id>` 형식이다.
2. 저장은 `RPUSH`, 소비는 `BLPOP`으로 동작한다.
3. `redis_ttl_seconds`가 있으면 키 TTL을 설정한다.

## 4. Worker / ThreadPool

1. `Worker`는 범용 큐 소비 워커다.
2. `ThreadPool`은 `Future` 기반 작업 실행기다.
3. 둘 다 공용 유틸로 제공되지만 현재 기본 채팅 조립에서는 직접 사용하지 않는다.

## 5. 유지보수 포인트

1. 큐와 버퍼는 `put/get/size/close`, `push/pop/cleanup/size` 계약을 유지해야 상위 변경을 줄일 수 있다.
2. `InMemoryEventBuffer`의 TTL/GC 설정이 부적절하면 메모리 사용량이 커질 수 있다.
3. Redis 구현은 연결 시점에 의존성 누락을 드러내므로 조용한 fallback이 없다.
4. 이벤트 `metadata`는 `dict` 또는 `None`만 허용한다.

## 6. 관련 문서

- `docs/shared/chat/services/service_executor.md`
- `docs/api/chat.md`
