# Shared Runtime

`src/single_request_tool_agent/shared/runtime`는 Queue, Buffer, Worker, ThreadPool 같은 범용 실행 유틸을 제공한다.

## 1. 현재 위치

이 모듈들은 여전히 `src`에 존재하지만, 기본 `/agent` 런타임은 직접 사용하지 않는다.

현재 기본 실행 경로:

```text
HTTP /agent
  -> AgentService
  -> Agent Graph
  -> 단일 JSON 응답
```

즉, 기본 런타임은 Queue/EventBuffer/Worker 없이 동작한다.

## 2. 제공 구성요소

| 분류 | 파일 | 역할 |
| --- | --- | --- |
| 런타임 공개 API | `src/single_request_tool_agent/shared/runtime/__init__.py` | Queue/Buffer/Worker/ThreadPool 공개 |
| Queue 모델 | `src/single_request_tool_agent/shared/runtime/queue/model.py` | `QueueConfig`, `QueueItem` |
| InMemory Queue | `src/single_request_tool_agent/shared/runtime/queue/in_memory_queue.py` | 프로세스 내부 큐 |
| Redis Queue | `src/single_request_tool_agent/shared/runtime/queue/redis_queue.py` | Redis 리스트 기반 큐 |
| Buffer 모델 | `src/single_request_tool_agent/shared/runtime/buffer/model.py` | `EventBufferConfig`, `StreamEventItem` |
| InMemory Buffer | `src/single_request_tool_agent/shared/runtime/buffer/in_memory_buffer.py` | 요청 버킷 기반 이벤트 버퍼 |
| Redis Buffer | `src/single_request_tool_agent/shared/runtime/buffer/redis_buffer.py` | Redis 기반 이벤트 버퍼 |
| Worker | `src/single_request_tool_agent/shared/runtime/worker/worker.py` | 큐 소비 워커 |
| ThreadPool | `src/single_request_tool_agent/shared/runtime/thread_pool/thread_pool.py` | 태스크 제출/종료 |

## 3. 언제 쓰는가

다음과 같은 커스텀 확장이 필요할 때만 직접 조립한다.

1. 비동기 작업 큐를 별도로 두고 싶을 때
2. 요청 단위 이벤트 버퍼/SSE를 다시 도입하고 싶을 때
3. 백그라운드 워커/스레드풀 유틸을 재사용하고 싶을 때

## 4. 문서 해석 기준

이 문서는 “현재 기본 런타임 동작 설명”이 아니라 “`shared/runtime` 모듈 자체의 기능 설명”으로 읽어야 한다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/agent/overview.md`
- `docs/api/agent.md`
