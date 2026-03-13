# History Repository

## 개요

`src/plan_and_then_execute_agent/shared/chat/repositories/history_repository.py` 구현을 기준으로 현재 동작을 정리한다.

채팅 세션/메시지/요청 커밋을 영속화합니다.
`db_client` 주입이 없으면 기본 SQLite 엔진을 내부 생성합니다.

## 주요 기능

1. 세션: `create_session`, `ensure_session`, `get_session`, `list_sessions`, `delete_session`
2. 메시지: `append_message`, `list_messages`
3. 멱등성: `is_request_committed`, `mark_request_committed`
4. 스키마 초기화: 세션/메시지/요청커밋 컬렉션 생성

## 동작 특성

- `append_message()` 시 세션 `message_count`, `updated_at`, `last_message_preview`를 함께 갱신합니다.
- request_id 커밋 컬렉션으로 assistant 응답 중복 저장을 방지합니다.

## 실패 경로

- `CHAT_MESSAGE_EMPTY`
- `CHAT_REQUEST_ID_EMPTY`
- 저장소 예외는 `CHAT_*_ERROR` 코드로 래핑됩니다.

## 관련 문서

- `docs/shared/chat/repositories/schemas/session_schema.md`
- `docs/shared/chat/repositories/schemas/message_schema.md`
- `docs/shared/chat/repositories/schemas/request_commit_schema.md`
- `docs/shared/chat/services/chat_service.md`
