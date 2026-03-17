# Chat Service

## 개요

`src/single_request_tool_agent/shared/agent/services/chat_service.py` 구현을 기준으로 현재 동작을 정리한다.

저장소(`ChatHistoryRepository`)와 그래프(`GraphPort`)를 결합해 채팅 유스케이스를 수행합니다.
세션 관리, 문맥 빌드, 동기/비동기 실행, request_id 멱등 저장을 담당합니다.

## 주요 메서드

1. 세션/메시지: `create_session`, `list_sessions`, `get_session`, `list_messages`, `delete_session`
2. 실행: `invoke`, `ainvoke`
3. 저장: `append_assistant_message`, `persist_assistant_message`

## 실행 동작

- 사용자 메시지를 먼저 저장한 뒤 문맥(`_build_context_history`)을 구성합니다.
- `GraphPort.invoke/ainvoke`를 호출해 최종 응답 본문을 받아 assistant 메시지로 저장합니다.
- request_id가 있으면 `persist_assistant_message()`가 멱등 저장을 담당합니다.

## 실패 경로

- `CHAT_SESSION_NOT_FOUND`
- `CHAT_MESSAGE_EMPTY`
- `CHAT_STREAM_EMPTY`

## 관련 문서

- `docs/shared/agent/interface/ports.md`
- `docs/shared/agent/graph/base_chat_graph.md`
- `docs/shared/agent/memory/session_store.md`
- `docs/shared/agent/repositories/history_repository.md`
