# `interface/ports.py` 레퍼런스

이 파일은 채팅 실행 계층의 포트 계약을 `Protocol`로 정의한다. 구현체를 바꾸더라도 API 조립 코드가 같은 형태로 의존하도록 만드는 목적이다.

## 1. 코드 설명

정의된 타입:

1. `StreamNodeConfig`
2. `GraphPort`
3. `ChatServicePort`
4. `ServiceExecutorPort`

핵심 메서드:

| 포트 | 주요 메서드 |
| --- | --- |
| `GraphPort` | `compile`, `set_stream_node`, `invoke`, `ainvoke`, `stream_events`, `astream_events` |
| `ChatServicePort` | `create_session`, `list_sessions`, `list_messages`, `delete_session`, `persist_assistant_message`, `stream`, `astream` |
| `ServiceExecutorPort` | `submit_job`, `stream_events`, `get_session_status` |

현재 구현체 매핑:

1. `GraphPort` -> `BaseChatGraph`
2. `ChatServicePort` -> `ChatService`
3. `ServiceExecutorPort` -> `ServiceExecutor`

## 2. 유지보수 포인트

1. 포트 시그니처를 바꾸면 구현체뿐 아니라 `runtime.py` 조립 코드와 API 라우터 의존성 주입 함수까지 함께 수정해야 한다.
2. 반환 타입을 느슨하게 `Any`로 둔 부분이 많아서, 문서와 구현이 어긋나기 쉽다. 타입을 강화할 때는 호출 체인 전체를 점검해야 한다.

## 3. 추가 개발/확장 가이드

1. 새로운 실행기나 그래프 구현을 도입할 때는 먼저 이 포트 계약을 만족시키는지 확인해야 한다.
2. 포트를 세분화하고 싶다면 실제 두 개 이상의 구현체가 필요한 시점까지는 현재 계약을 유지하는 편이 안정적이다.

## 4. 관련 코드

- `src/chatbot/shared/chat/graph/base_chat_graph.py`
- `src/chatbot/shared/chat/services/chat_service.py`
- `src/chatbot/shared/chat/services/service_executor.py`
