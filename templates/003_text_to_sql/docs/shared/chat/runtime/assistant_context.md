# runtime/assistant_context.py

세션별 직전 assistant 응답 컨텍스트 캐시를 정의하는 모듈이다.

## 1. 역할

- `AssistantContext` 모델로 직전 응답 본문과 `answer_source_meta`를 저장한다.
- 캐시 포트(`AssistantContextStore`)와 두 구현체(`InMemory`, `Redis`)를 제공한다.

## 2. 주요 구성

| 구성 | 설명 |
| --- | --- |
| `AssistantContext` | `session_id`, `request_id`, `content`, `answer_source_meta`, `created_at` |
| `AssistantContextStore` | `set/get/clear_session/close` 포트 |
| `InMemoryAssistantContextStore` | TTL + LRU 기반 인메모리 캐시 |
| `RedisAssistantContextStore` | Redis key + sorted set 기반 TTL/LRU 캐시 |

## 3. 동작 규칙

- InMemory는 `OrderedDict`와 `touched_at`을 사용해 만료/축출을 수행한다.
- Redis는 컨텍스트 key와 LRU index key를 함께 유지한다.
- 조회 성공 시 touch 갱신으로 TTL/LRU를 연장한다.

## 4. 실패 경로

- Redis 패키지 미설치: `RuntimeError`
- Redis host/port/db 설정 오류: `RuntimeError`
- Redis ping 비정상: `RuntimeError`

## 5. 관련 코드

- `runtime/assistant_context_runtime_store.py`
- `services/service_executor.py`
