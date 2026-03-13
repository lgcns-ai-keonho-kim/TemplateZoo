# Shared Chat 가이드

이 문서는 `src/rag_chatbot/shared/chat` 패키지가 채팅 실행 경로를 어떻게 조합하는지 설명한다.

## 1. 현재 구조

- `interface`: 그래프, 서비스, 실행기 포트
- `graph`: `BaseChatGraph`
- `memory`: `ChatSessionMemoryStore`
- `nodes`: 재사용 가능한 범용 노드
- `repositories`: `ChatHistoryRepository`와 스키마 팩토리
- `services`: `ChatService`, `ServiceExecutor`

## 2. 실행 흐름

1. `ServiceExecutor.submit_job()`이 작업을 큐에 넣는다.
2. 워커가 `ChatService.astream()`을 실행한다.
3. `BaseChatGraph`가 LangGraph 이벤트를 표준 이벤트로 바꾼다.
4. `ServiceExecutor`가 `start/token/references/done/error`로 정규화해 버퍼에 적재한다.
5. done 후 assistant 응답은 request_id 멱등 규칙에 따라 한 번만 저장한다.

## 3. 유지보수/추가개발 포인트

- 세션 저장 정책을 바꾸면 repository와 service, executor 후처리를 함께 수정해야 한다.
- 노드 추가나 stream 이벤트 추가는 `BaseChatGraph`와 `ServiceExecutor`까지 연쇄 영향을 준다.
- 이 계층은 현재 프로세스 로컬 메모리와 큐를 사용하므로 멀티 인스턴스 운영을 전제로 기능을 추가하면 안 된다.

## 4. 관련 문서

- `docs/shared/chat/interface/ports.md`
- `docs/shared/chat/graph/base_chat_graph.md`
- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/shared/runtime.md`
