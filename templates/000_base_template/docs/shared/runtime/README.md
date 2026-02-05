# 런타임 구성 가이드

이 문서는 `src/base_template/shared/runtime` 모듈의 큐, 워커, 스레드풀 사용법을 설명합니다.

**구성 요소**
- 큐: `InMemoryQueue`, `RedisQueue`, `QueueConfig`, `QueueItem`
- 워커: `Worker`, `WorkerConfig`, `WorkerState`
- 스레드풀: `ThreadPool`, `ThreadPoolConfig`, `TaskRecord`

## 인메모리 큐

**설명**
- 표준 `queue.Queue` 기반으로 블로킹/타임아웃을 지원합니다.
- 종료 시 센티널을 넣어 소비자 루프를 안전하게 종료합니다.

**기본 사용법**

```python
from base_template.shared.runtime.queue import InMemoryQueue, QueueConfig

queue = InMemoryQueue(QueueConfig(max_size=100, default_timeout=1.0))
item = queue.put({"job": 1})
received = queue.get()
queue.close()
```

## Redis 큐

**설명**
- Redis 리스트를 사용해 큐를 구현합니다.
- `blpop` 기반으로 블로킹 소비를 제공합니다.

**기본 사용법**

```python
from base_template.shared.runtime.queue import RedisQueue, QueueConfig

queue = RedisQueue(url="redis://localhost:6379/0", name="jobs", config=QueueConfig(max_size=100))
queue.put({"job": 1})
item = queue.get()
queue.close()
```

**주의 사항**
- JSON 직렬화가 가능한 payload만 저장할 수 있습니다.
- `max_size`는 주기적 폴링 기반으로 확인합니다.

## 워커

**설명**
- 큐에서 아이템을 꺼내 처리하는 워커입니다.
- 데코레이터와 `with` 문을 모두 지원합니다.

**기본 사용법**

```python
from base_template.shared.runtime.queue import InMemoryQueue
from base_template.shared.runtime.worker import Worker, WorkerConfig

queue = InMemoryQueue()
worker = Worker(queue, WorkerConfig(name="consumer", poll_timeout=0.5))

@worker
def handle(item):
    print(item.payload)

with worker:
    queue.put({"task": "A"})
```

**재시도/중단 정책**
- `max_retries`만큼 실패 시 재시도합니다.
- `stop_on_error=True`면 오류 발생 시 워커를 중단합니다.

**주의 사항**
- 현재 워커는 `InMemoryQueue` 타입을 기준으로 작성되어 있습니다.
- Redis 큐를 사용하려면 인터페이스 호환을 확인하고 테스트가 필요합니다.

## 스레드풀

**설명**
- `ThreadPoolExecutor`를 감싸서 간단한 실행 인터페이스를 제공합니다.
- 데코레이터와 `with` 문을 모두 지원합니다.

**기본 사용법**

```python
from base_template.shared.runtime.thread_pool import ThreadPool

with ThreadPool() as pool:
    future = pool.submit(lambda x: x + 1, 1)
    print(future.result())
```

**데코레이터 사용**

```python
pool = ThreadPool()

@pool.task
def work(x):
    return x * 2

future = work(3)
print(future.result())
```
