# Shared Chat 모듈 레퍼런스

`src/chatbot/shared/chat`은 채팅 실행을 공통 계층에서 감싸는 패키지다. 그래프 실행 포트, 공용 노드, 메모리 캐시, 저장소, 서비스 오케스트레이션을 포함한다.

## 1. 구조

| 경로 | 역할 | 대표 파일 |
| --- | --- | --- |
| `graph` | LangGraph 실행 공통화 | `graph/base_chat_graph.py` |
| `interface` | 그래프/서비스/실행기 포트 | `interface/ports.py` |
| `memory` | 세션 최근 메시지 캐시 | `memory/session_store.py` |
| `nodes` | 범용 노드 | `nodes/llm_node.py`, `nodes/branch_node.py`, `nodes/message_node.py` |
| `repositories` | 세션/메시지 이력 저장 | `repositories/history_repository.py` |
| `services` | 실행 서비스와 비동기 오케스트레이터 | `services/chat_service.py`, `services/service_executor.py` |

## 2. 공개 API

`src/chatbot/shared/chat/__init__.py`가 외부로 노출하는 대표 항목:

1. 타입/포트: `StreamNodeConfig`, `GraphPort`, `ChatServicePort`, `ServiceExecutorPort`
2. 그래프 실행기: `BaseChatGraph`
3. 메모리 저장소: `ChatSessionMemoryStore`
4. 영속 저장소: `ChatHistoryRepository`
5. 서비스: `ChatService`, `ServiceExecutor`
6. 스키마 팩토리: `build_chat_session_schema`, `build_chat_message_schema`, `build_chat_request_commit_schema`

## 3. 실행 흐름

```text
API Router
 -> ServiceExecutor
 -> ChatService
 -> BaseChatGraph
 -> core/chat nodes
 -> ChatHistoryRepository
```

## 4. 유지보수 포인트

1. `ChatService.stream()`은 `token` 우선, `assistant_message` fallback 구조다.
2. `ServiceExecutor`는 `blocked` 노드의 `assistant_message`를 공개 `token` 이벤트로 변환한다.
3. `ChatHistoryRepository`는 기본적으로 SQLite를 사용하지만 `DBClient` 주입으로 다른 엔진으로 바꿀 수 있다.
4. `request_id`는 저장 멱등성과 SSE 구독을 동시에 연결한다.

## 5. 상세 문서

- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/shared/chat/repositories/history_repository.md`
