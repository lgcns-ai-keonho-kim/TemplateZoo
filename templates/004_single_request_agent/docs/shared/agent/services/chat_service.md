# Chat Service

## 개요

`src/single_request_agent/shared/agent/services/chat_service.py` 구현을 기준으로 현재 동작을 정리한다.

저장소(`ChatHistoryRepository`)와 그래프(`GraphPort`)를 결합해 채팅 유스케이스를 수행합니다.
세션 관리, 문맥 빌드, 스트림 결과 정규화, request_id 멱등 저장을 담당합니다.

## 주요 메서드

1. 세션/메시지: `create_session`, `list_sessions`, `get_session`, `list_messages`, `delete_session`
2. 실행: `invoke`, `ainvoke`, `stream`, `astream`
3. 저장: `append_assistant_message`, `persist_assistant_message`

## 실행 동작

- 사용자 메시지를 먼저 저장한 뒤 문맥(`_build_context_history`)을 구성합니다.
- 스트림에서는 `token` 누적 + `assistant_message` fallback으로 최종 본문을 확정합니다.
- 완료 시 `references`와 `done` 이벤트를 보강해 상위 실행기에서 일관되게 처리할 수 있게 합니다.

## 실패 경로

- `CHAT_SESSION_NOT_FOUND`
- `CHAT_MESSAGE_EMPTY`
- `CHAT_STREAM_EMPTY`

## 관련 문서

- `docs/shared/agent/interface/ports.md`
- `docs/shared/agent/graph/base_chat_graph.md`
- `docs/shared/agent/memory/session_store.md`
- `docs/shared/agent/repositories/history_repository.md`
