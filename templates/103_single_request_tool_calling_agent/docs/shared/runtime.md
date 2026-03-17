# Shared Runtime

`src/single_request_tool_agent/shared/runtime`는 Queue, Worker, ThreadPool 같은 범용 실행 유틸을 제공한다.

## 1. 모듈 역할

이 모듈은 상위 서비스가 HTTP 요청 처리 이후 비동기 작업 분배와 백그라운드 실행 흐름을 조립할 때 사용할 수 있는 공용 런타임 구성요소를 담고 있다.

## 2. 제공 구성요소

| 분류 | 파일 | 역할 |
| --- | --- | --- |
| 런타임 공개 API | `src/single_request_tool_agent/shared/runtime/__init__.py` | Queue/Worker/ThreadPool 공개 |
| Queue 모델 | `src/single_request_tool_agent/shared/runtime/queue/model.py` | `QueueConfig`, `QueueItem` |
| InMemory Queue | `src/single_request_tool_agent/shared/runtime/queue/in_memory_queue.py` | 프로세스 내부 큐 |
| Redis Queue | `src/single_request_tool_agent/shared/runtime/queue/redis_queue.py` | Redis 리스트 기반 큐 |
| Worker | `src/single_request_tool_agent/shared/runtime/worker/worker.py` | 큐 소비 워커 |
| ThreadPool | `src/single_request_tool_agent/shared/runtime/thread_pool/thread_pool.py` | 태스크 제출/종료 |

## 3. 언제 쓰는가

다음과 같은 실행 구성이 필요할 때 직접 조립한다.

1. 비동기 작업 큐를 별도로 두고 싶을 때
2. 백그라운드 워커를 붙여 제한된 병렬도로 작업을 처리하고 싶을 때
3. 스레드풀 유틸을 재사용하고 싶을 때

## 4. 문서 해석 기준

이 문서는 `shared/runtime` 하위 모듈의 역할과 조합 지점을 설명한다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/agent/overview.md`
- `docs/api/agent.md`
