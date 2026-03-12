# Shared Chat 모듈 레퍼런스

`src/chatbot/shared/chat`은 채팅 실행을 공통 계층에서 감싸는 패키지다. 그래프 실행 포트, 공용 노드, 메모리 캐시, 저장소, 서비스 오케스트레이션을 포함한다.

## 1. 코드 설명

| 경로 | 역할 | 대표 파일 |
| --- | --- | --- |
| `graph` | LangGraph 실행 공통화 | `graph/base_chat_graph.py` |
| `interface` | 그래프/서비스/실행기 포트 | `interface/ports.py` |
| `memory` | 세션 최근 메시지 캐시 | `memory/session_store.py` |
| `nodes` | 재사용 가능한 범용 노드 | `nodes/llm_node.py`, `nodes/branch_node.py` |
| `repositories` | 세션/메시지 이력 저장 | `repositories/history_repository.py` |
| `services` | 실제 실행 서비스와 비동기 실행기 | `services/chat_service.py`, `services/service_executor.py` |

실행 흐름은 다음과 같다.

```text
API Router
 -> ServiceExecutor
 -> ChatService
 -> BaseChatGraph
 -> core/chat/nodes
 -> ChatHistoryRepository
```

## 2. 공개 API

`src/chatbot/shared/chat/__init__.py`가 외부로 노출하는 항목:

1. 타입/포트: `StreamNodeConfig`, `GraphPort`, `ChatServicePort`, `ServiceExecutorPort`
2. 그래프 실행기: `BaseChatGraph`
3. 메모리 저장소: `ChatSessionMemoryStore`
4. 영속 저장소: `ChatHistoryRepository`
5. 서비스: `ChatService`, `ServiceExecutor`
6. 스키마 팩토리: `build_chat_session_schema`, `build_chat_message_schema`, `build_chat_request_commit_schema`

## 3. 유지보수 포인트

1. `ChatService.stream()`은 `token` 이벤트 누적과 `assistant_message` fallback을 함께 처리한다. 그래프 이벤트 정책을 바꾸면 이 해석 로직도 같이 봐야 한다.
2. `ServiceExecutor`는 `blocked` 노드의 `assistant_message`를 `token`으로 변환한다. 따라서 노드명이나 이벤트명을 변경하면 SSE 표준화가 깨질 수 있다.
3. `ChatHistoryRepository`는 기본적으로 SQLite를 사용하지만, 생성자에 `DBClient`를 주입하면 다른 엔진으로 전환할 수 있다.

## 4. 추가 개발/확장 가이드

1. 새 그래프를 붙일 때는 `GraphPort`만 만족하면 `ChatService`를 재사용할 수 있다.
2. 세션 메모리 정책을 바꿀 때는 `ChatSessionMemoryStore`와 `CHAT_MEMORY_MAX_MESSAGES` 환경 변수를 함께 점검해야 한다.
3. 저장 포맷을 바꿀 때는 저장소, 스키마, API 응답, UI 표시 순서를 동시에 점검해야 한다.

## 5. 상세 문서

- `docs/shared/chat/graph/base_chat_graph.md`
- `docs/shared/chat/interface/ports.md`
- `docs/shared/chat/memory/session_store.md`
- `docs/shared/chat/nodes/_state_adapter.md`
- `docs/shared/chat/nodes/branch_node.md`
- `docs/shared/chat/nodes/fanout_branch_node.md`
- `docs/shared/chat/nodes/function_node.md`
- `docs/shared/chat/nodes/llm_node.md`
- `docs/shared/chat/nodes/message_node.md`
- `docs/shared/chat/repositories/history_repository.md`
- `docs/shared/chat/repositories/schemas/session_schema.md`
- `docs/shared/chat/repositories/schemas/message_schema.md`
- `docs/shared/chat/repositories/schemas/request_commit_schema.md`
- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/services/service_executor.md`
