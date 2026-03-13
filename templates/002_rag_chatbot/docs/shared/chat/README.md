# Shared Chat

## 구성

- `graph`: `BaseChatGraph`
- `memory`: `ChatSessionMemoryStore`
- `repositories`: `ChatHistoryRepository`
- `services`: `ChatService`, `ServiceExecutor`
- `nodes`: 범용 노드 유틸

## 실행 흐름

1. `ServiceExecutor.submit_job()`이 작업 큐에 요청을 넣는다.
2. 워커 스레드가 `ChatService.astream()`을 실행한다.
3. `BaseChatGraph`가 LangGraph 이벤트를 표준 이벤트로 변환한다.
4. `ServiceExecutor`가 `start`, `token`, `references`, `done`, `error`로 정규화해 이벤트 버퍼에 적재한다.
5. `done` 이후 assistant 응답은 `request_id` 멱등 규칙으로 한 번만 저장한다.

## 저장과 메모리

- 기본 저장소는 `ChatHistoryRepository(db_client=None)` 경로의 SQLite다.
- 메모리 캐시는 `CHAT_MEMORY_MAX_MESSAGES` 기준으로 최근 메시지를 유지한다.
- 세션 삭제 시 저장소 데이터와 메모리 캐시를 함께 비운다.

## 현재 범위

- 기본 실행 경로는 프로세스 로컬 메모리와 큐를 사용한다.
- 멀티 인스턴스 분산 런타임은 기본 조립에 포함되지 않는다.
