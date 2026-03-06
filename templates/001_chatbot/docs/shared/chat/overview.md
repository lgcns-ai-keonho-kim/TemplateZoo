# Shared Chat 모듈 레퍼런스

`src/chatbot/shared/chat`의 하위 모듈을 코드 구조와 같은 단위로 정리한 인덱스 문서다.

## 1. 디렉터리 매핑

| 코드 경로 | 문서 |
| --- | --- |
| `src/chatbot/shared/chat/graph/base_chat_graph.py` | `docs/shared/chat/graph/base_chat_graph.md` |
| `src/chatbot/shared/chat/interface/ports.py` | `docs/shared/chat/interface/ports.md` |
| `src/chatbot/shared/chat/memory/session_store.py` | `docs/shared/chat/memory/session_store.md` |
| `src/chatbot/shared/chat/nodes/*.py` | `docs/shared/chat/nodes/*.md` |
| `src/chatbot/shared/chat/repositories/history_repository.py` | `docs/shared/chat/repositories/history_repository.md` |
| `src/chatbot/shared/chat/repositories/schemas/*.py` | `docs/shared/chat/repositories/schemas/*.md` |
| `src/chatbot/shared/chat/services/*.py` | `docs/shared/chat/services/*.md` |

## 2. 패키지 공개 API (`__init__.py`)

`src/chatbot/shared/chat/__init__.py`는 아래 항목을 외부로 노출한다.

1. 포트/타입: `StreamNodeConfig`, `GraphPort`, `ChatServicePort`, `ServiceExecutorPort`
2. 그래프 실행: `BaseChatGraph`
3. 메모리 저장소: `ChatSessionMemoryStore`
4. 영속 저장소: `ChatHistoryRepository`
5. 서비스: `ChatService`, `ServiceExecutor`
6. 스키마 팩토리: `build_chat_session_schema`, `build_chat_message_schema`, `build_chat_request_commit_schema`

## 3. 실행 흐름 요약

```text
API Router
 -> ServiceExecutor (작업 큐/이벤트 버퍼)
 -> ChatService (세션/메시지 처리)
 -> BaseChatGraph (LangGraph 실행)
 -> Node 계층 (LLM/분기/메시지/함수)
 -> ChatHistoryRepository (DB 저장)
```

## 4. 모듈별 상세 문서

### 4-1. Graph

- `docs/shared/chat/graph/base_chat_graph.md`

### 4-2. Interface

- `docs/shared/chat/interface/ports.md`

### 4-3. Memory

- `docs/shared/chat/memory/session_store.md`

### 4-4. Nodes

- `docs/shared/chat/nodes/_state_adapter.md`
- `docs/shared/chat/nodes/branch_node.md`
- `docs/shared/chat/nodes/fanout_branch_node.md`
- `docs/shared/chat/nodes/function_node.md`
- `docs/shared/chat/nodes/llm_node.md`
- `docs/shared/chat/nodes/message_node.md`

### 4-5. Repositories

- `docs/shared/chat/repositories/history_repository.md`
- `docs/shared/chat/repositories/schemas/session_schema.md`
- `docs/shared/chat/repositories/schemas/message_schema.md`
- `docs/shared/chat/repositories/schemas/request_commit_schema.md`

### 4-6. Services

- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/services/service_executor.md`

## 5. 운영에서 먼저 보는 문서

1. SSE 지연/종료 이슈: `docs/shared/chat/services/service_executor.md`
2. 중복 저장/멱등성 이슈: `docs/shared/chat/services/chat_service.md`, `docs/shared/chat/repositories/history_repository.md`
3. 분기/노드 입력 오류: `docs/shared/chat/nodes/branch_node.md`, `docs/shared/chat/nodes/llm_node.md`, `docs/shared/chat/nodes/_state_adapter.md`
