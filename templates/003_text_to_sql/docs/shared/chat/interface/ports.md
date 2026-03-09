# interface/ports.py

`GraphPort`, `ChatServicePort`, `ServiceExecutorPort` 프로토콜을 정의하는 계약 모듈이다.

## 1. 역할

- 상위 계층이 구현체 타입에 결합되지 않도록 실행 계약을 분리한다.
- `shared/chat` 내부 조립(`BaseChatGraph`, `ChatService`, `ServiceExecutor`)의 최소 메서드 집합을 고정한다.

## 2. 주요 인터페이스

| 프로토콜 | 핵심 메서드 | 의미 |
| --- | --- | --- |
| `GraphPort` | `invoke/ainvoke`, `stream_events/astream_events` | 그래프 실행 포트 |
| `ChatServicePort` | 세션 CRUD + `stream/astream` + `persist_assistant_message` | 도메인 실행 서비스 포트 |
| `ServiceExecutorPort` | `submit_job`, `stream_events`, `get_session_status` | 비동기 실행 오케스트레이터 포트 |

## 3. 데이터 경계

- `GraphPort` 입력: `session_id`, `user_message`, `history`, `config`
- `ChatServicePort` 입력: 사용자 질의/세션 식별자/컨텍스트 윈도우
- `ServiceExecutorPort` 출력: `request_id` 기반 SSE 스트림

## 4. 구현체 매핑

- `GraphPort`: `shared/chat/graph/base_chat_graph.py`
- `ChatServicePort`: `shared/chat/services/chat_service.py`
- `ServiceExecutorPort`: `shared/chat/services/service_executor.py`
