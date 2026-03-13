# `repositories/history_repository.py` 레퍼런스

`ChatHistoryRepository`는 세션, 메시지, request commit 이력을 저장하는 저장소 구현체다.

## 1. 핵심 메서드

1. 세션: `create_session`, `ensure_session`, `get_session`, `list_sessions`, `delete_session`
2. 메시지: `append_message`, `list_messages`, `get_recent_messages`
3. 멱등성: `is_request_committed`, `mark_request_committed`

## 2. 기본 초기화

1. `db_client`를 주입하지 않으면 `SQLiteEngine(database_path)`를 생성한다.
2. 세션/메시지/request commit 스키마를 보장한다.
3. 메시지 저장 시 세션의 `message_count`, `updated_at`, `last_message_preview`도 함께 갱신한다.

## 3. 주요 오류 코드

1. `CHAT_MESSAGE_EMPTY`
2. `CHAT_REQUEST_ID_EMPTY`
3. `CHAT_SESSION_CREATE_ERROR`
4. `CHAT_SESSION_GET_ERROR`
5. `CHAT_SESSION_LIST_ERROR`
6. `CHAT_SESSION_DELETE_ERROR`
7. `CHAT_MESSAGE_APPEND_ERROR`
8. `CHAT_MESSAGE_LIST_ERROR`
9. `CHAT_MESSAGE_RECENT_ERROR`
10. `CHAT_REQUEST_COMMIT_GET_ERROR`
11. `CHAT_REQUEST_COMMIT_UPSERT_ERROR`

## 4. 유지보수 포인트

1. `append_message()`는 세션 요약 필드까지 같이 갱신한다.
2. request commit 컬렉션은 `persist_assistant_message()` 멱등성의 핵심이다.
3. `get_recent_messages()`는 최근 메시지를 최신 순으로 읽은 뒤 다시 시간 순으로 뒤집어 반환한다.
4. 기본 경로는 SQLite지만 `DBClient` 주입으로 다른 엔진으로 전환할 수 있다.

## 5. 관련 문서

- `docs/shared/chat/services/chat_service.md`
- `docs/integrations/db/overview.md`
