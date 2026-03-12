# Shared Runtime 레퍼런스

`src/chatbot/shared/runtime`은 큐, 이벤트 버퍼, 워커, 스레드풀을 제공하는 공통 런타임 유틸 계층이다.

## 1. 코드 설명

구성 요소:

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

`Worker`, `ThreadPool`은 공용 유틸로 제공되지만 현재 기본 채팅 조립에서는 직접 사용하지 않는다.

### 1-1. Queue

1. `InMemoryQueue`는 `queue.Queue` 기반
2. `RedisQueue`는 `rpush/blpop` 기반
3. 둘 다 `QueueItem`을 처리 단위로 사용

### 1-2. EventBuffer

1. `InMemoryEventBuffer`는 `session_id:request_id` 버킷 키 사용
2. `RedisEventBuffer`는 `<prefix>:<session_id>:<request_id>` 키 사용
3. 둘 다 `StreamEventItem`을 저장 단위로 사용

### 1-3. Worker / ThreadPool

1. `Worker`는 큐를 소비하는 범용 워커
2. `ThreadPool`은 `Future` 기반 비동기 실행기

## 2. 유지보수 포인트

1. `RedisQueue`와 `RedisEventBuffer`는 `redis` 패키지가 없으면 즉시 `RuntimeError`를 발생시킨다.
2. `InMemoryEventBuffer`는 TTL과 GC 주기 설정이 부적절하면 메모리 사용량이 커질 수 있다.
3. `Worker.stop()`은 내부 큐를 닫는다. 여러 소비자가 같은 큐를 공유하는 구조로 확장할 때는 현재 종료 정책을 다시 봐야 한다.
4. `ThreadPool.submit()`은 executor가 없으면 자동 초기화한다. 수명주기를 명시적으로 통제하고 싶다면 with 문 사용이 더 분명하다.

## 3. 추가 개발/확장 가이드

1. Redis 전환은 구현체가 아니라 조립 코드에서 선택하도록 유지하는 편이 테스트와 운영 분리가 쉽다.
2. 새로운 버퍼나 큐 백엔드를 추가할 때는 현재 메서드 집합(`put/get/size/close`, `push/pop/cleanup/size`)을 유지하면 상위 변경을 줄일 수 있다.
3. 고부하 환경에서 이벤트 적체가 문제라면 먼저 `EventBufferConfig.max_size`, TTL, 소비 속도부터 점검하는 것이 현실적이다.

## 4. 관련 코드

- `src/chatbot/shared/chat/services/service_executor.py`
- `src/chatbot/api/chat/services/runtime.py`
