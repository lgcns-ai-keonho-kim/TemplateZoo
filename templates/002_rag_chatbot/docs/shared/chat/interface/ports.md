# Shared Chat Interface Ports

이 문서는 `src/rag_chatbot/shared/chat/interface/ports.py`의 포트 인터페이스를 설명한다.

## 1. 목적

- 상위 계층(API)과 하위 구현(graph/service/executor) 사이의 호출 계약을 고정한다.
- 구현체 교체 시 상위 호출 코드의 변경 범위를 줄인다.

## 2. 타입

| 타입 | 설명 |
| --- | --- |
| `StreamNodeConfig` | 노드별 허용 이벤트 목록 매핑 타입 (`Mapping[str, str | Sequence[str]]`) |

## 3. GraphPort

주요 메서드:

1. `compile(checkpointer=None)`
2. `set_stream_node(stream_node)`
3. `invoke(...)`, `ainvoke(...)`
4. `stream_events(...)`, `astream_events(...)`

역할:

- 그래프 컴파일과 실행을 표준 인터페이스로 제공한다.
- 노드/이벤트 필터 정책(`stream_node`) 변경 지점을 단일화한다.

## 4. ChatServicePort

주요 메서드:

1. 세션/메시지 API: `create_session`, `list_sessions`, `get_session`, `list_messages`, `delete_session`
2. 실행 API: `invoke`, `ainvoke`, `stream`, `astream`
3. 저장 API: `persist_assistant_message`

역할:

- 세션 이력 저장과 그래프 실행을 하나의 서비스 경계로 묶는다.
- UI API와 Chat API가 동일 도메인 모델을 공유하도록 한다.

## 5. ServiceExecutorPort

주요 메서드:

1. `submit_job(session_id, user_query, context_window)`
2. `stream_events(session_id, request_id)`
3. `get_session_status(session_id)`

역할:

- 비동기 작업 처리와 SSE 이벤트 전달 경계를 정의한다.
- 라우터 계층이 큐/버퍼 구현 세부사항에 의존하지 않도록 한다.

## 6. 관련 문서

- `docs/shared/chat/services/chat_service.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/shared/chat/graph/base_chat_graph.md`
