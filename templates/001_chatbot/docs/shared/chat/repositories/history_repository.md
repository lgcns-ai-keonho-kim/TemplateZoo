# `repositories/history_repository.py` 레퍼런스

`ChatHistoryRepository`는 세션, 메시지, request commit 이력을 저장하는 저장소 구현체다. 기본값은 SQLite지만, `DBClient`를 주입하면 다른 엔진으로도 동작한다.

## 1. 코드 설명

핵심 메서드:

1. 세션: `create_session`, `ensure_session`, `get_session`, `list_sessions`, `delete_session`
2. 메시지: `append_message`, `list_messages`, `get_recent_messages`
3. 멱등성: `is_request_committed`, `mark_request_committed`

기본 초기화:

1. `db_client` 미주입 시 `SQLiteEngine(database_path)` 생성
2. `create_collection()`으로 세션/메시지/request commit 스키마 보장
3. 메시지 저장 시 세션의 `message_count`, `updated_at`, `last_message_preview`를 함께 갱신

주요 오류 코드:

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

## 2. 유지보수 포인트

1. `append_message()`는 세션 요약 필드까지 같이 갱신한다. 메시지 저장 경로를 분리하면 세션 목록 정렬과 미리보기가 틀어질 수 있다.
2. request commit 컬렉션은 `persist_assistant_message()`의 멱등성 보장 핵심이므로, 저장 시점을 바꾸면 중복 응답 저장 가능성이 생긴다.
3. `get_recent_messages()`는 DESC 조회 후 reverse 한다. 최근 메시지 조회 정렬을 바꾸면 문맥 구성 순서가 바뀐다.

## 3. 추가 개발/확장 가이드

1. 다른 DB 엔진으로 전환할 때는 `DBClient` 계약과 스키마 생성 흐름만 유지하면 저장소 코드는 그대로 둘 수 있다.
2. 세션 삭제 시 request commit까지 같이 지울지 여부는 현재 구현에 없다. 운영 요구가 생기면 삭제 정책을 명시적으로 추가해야 한다.

## 4. 관련 코드

- `src/chatbot/shared/chat/services/chat_service.py`
- `src/chatbot/shared/chat/repositories/schemas/session_schema.py`
- `src/chatbot/shared/chat/repositories/schemas/message_schema.py`
- `src/chatbot/shared/chat/repositories/schemas/request_commit_schema.py`
