# Interface Ports 문서

대상 코드: `src/plan_and_then_execute_agent/shared/chat/interface/ports.py`

## 역할

`shared/chat` 계층의 포트(Protocol) 계약을 정의합니다.
구현체(`ChatService`, `ServiceExecutor`, `BaseChatGraph`)는 이 계약을 기준으로 조립됩니다.

## 주요 타입

1. `StreamNodeConfig`: 스트림 노드 정책 타입 별칭
2. `GraphPort`: 그래프 컴파일/실행/스트림 인터페이스
3. `ChatServicePort`: 세션 CRUD, 실행, 멱등 저장 인터페이스
4. `ServiceExecutorPort`: 작업 제출, SSE 스트림, 상태 조회 인터페이스

## 인터페이스 경계

- `GraphPort`는 `invoke/ainvoke`와 `stream_events/astream_events`를 모두 제공합니다.
- `ChatServicePort`는 `persist_assistant_message`를 통해 request_id 멱등 저장을 노출합니다.
- `ServiceExecutorPort`는 HTTP 라우터가 직접 의존하는 최소 표면입니다.

## 연관 문서

- `docs/shared/chat/graph/base_chat_graph.md`
- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/services/service_executor.md`
