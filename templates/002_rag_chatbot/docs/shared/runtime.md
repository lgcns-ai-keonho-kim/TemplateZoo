# Shared Runtime 가이드

이 문서는 큐, 이벤트 버퍼, 워커, 스레드풀로 구성된 실행 인프라의 현재 구조를 설명한다.

## 1. 현재 구성

- `queue`: `InMemoryQueue`, `RedisQueue`, `QueueConfig`, `QueueItem`
- `buffer`: `InMemoryEventBuffer`, `RedisEventBuffer`, `EventBufferConfig`, `StreamEventItem`
- `worker`: `Worker`
- `thread_pool`: `ThreadPool`

## 2. 현재 기본 조립

- 실제 API 런타임은 현재 `InMemoryQueue`와 `InMemoryEventBuffer`를 고정 사용한다.
- Redis 구현은 모듈로 존재하지만, 조립 단계에서 선택하지 않으면 활성화되지 않는다.

## 3. 이벤트 버퍼 계약

- 내부 이벤트 타입은 `start`, `token`, `references`, `done`, `error`다.
- 버퍼 키는 요청 단위(`session_id`, `request_id`)로 분리된다.
- InMemory 버퍼는 TTL과 GC 주기를 사용하고, Redis 버퍼는 prefix와 TTL을 사용한다.

## 4. 유지보수/추가개발 포인트

- 큐/버퍼 백엔드를 교체할 때는 구현체뿐 아니라 `api/chat/services/runtime.py` 조립과 timeout 기본값을 함께 조정해야 한다.
- 새 내부 이벤트 필드를 추가하면 `StreamEventItem`, `ServiceExecutor`, 프런트 이벤트 소비자까지 연쇄 영향을 준다.
- 프로세스 종료 시 close/shutdown 동작이 누락되면 SSE가 매달리거나 워커가 남을 수 있다.

## 5. 관련 문서

- `docs/shared/chat/services/service_executor.md`
- `docs/shared/config.md`
- `docs/api/chat.md`
