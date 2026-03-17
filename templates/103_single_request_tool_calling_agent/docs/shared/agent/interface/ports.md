# Interface Ports

## 개요

`src/single_request_tool_agent/shared/agent/interface/ports.py` 구현을 기준으로 현재 동작을 정리한다.

`shared/agent` 계층의 포트(Protocol) 계약을 정의합니다.
구현체(`ChatService`, `BaseChatGraph`)는 이 계약을 기준으로 조립됩니다.

## 주요 타입

1. `StreamNodeConfig`: 스트림 노드 정책 타입 별칭
2. `GraphPort`: 그래프 컴파일/실행/스트림 인터페이스
3. `ChatServicePort`: 세션 CRUD, 실행, 멱등 저장 인터페이스

## 인터페이스 경계

- `GraphPort`는 `invoke/ainvoke`와 `stream_events/astream_events`를 모두 제공합니다.
- `ChatServicePort`는 `persist_assistant_message`를 통해 request_id 멱등 저장을 노출합니다.
- 현재 기본 `/agent` 라우터는 `AgentService`를 직접 사용하며, `GraphPort`의 이벤트는 내부 집계 용도로만 사용합니다.

## 관련 문서

- `docs/shared/agent/graph/base_chat_graph.md`
- `docs/shared/agent/services/chat_service.md`
