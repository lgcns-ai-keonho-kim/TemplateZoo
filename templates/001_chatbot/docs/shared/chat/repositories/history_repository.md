# `repositories/history_repository.py` 레퍼런스

## 1. 모듈 목적

`ChatHistoryRepository`는 세션/메시지/요청 커밋을 DB에 저장하는 저장소 구현체다.

- 기본 동작: SQLite (`db_client` 미주입)
- 주입 동작: 외부 `DBClient` 사용 (PostgreSQL/MongoDB 등)

## 2. 핵심 클래스

1. `ChatHistoryRepository`
- 세션: `create_session`, `ensure_session`, `get_session`, `list_sessions`, `delete_session`
- 메시지: `append_message`, `list_messages`, `get_recent_messages`
- 멱등성: `is_request_committed`, `mark_request_committed`

## 3. 입력/출력

1. 생성자
- `db_client`가 없으면 `SQLiteEngine(database_path)`를 생성
- 시작 시 `_initialize()`로 컬렉션 스키마를 보장

2. `append_message`
- 입력: `session_id`, `role`, `content`, `metadata`
- 처리: 메시지 upsert + 세션 카운트/미리보기 갱신
- 출력: `ChatMessage`

3. `delete_session`
- 출력: `(deleted: bool, deleted_message_count: int)`

## 4. 실패 경로

1. `CHAT_MESSAGE_EMPTY`
- 조건: `append_message`에 빈 본문

2. `CHAT_REQUEST_ID_EMPTY`
- 조건: `is_request_committed`, `mark_request_committed`의 `request_id` 공백

3. 저장소 래핑 오류
- `CHAT_SESSION_CREATE_ERROR`
- `CHAT_SESSION_GET_ERROR`
- `CHAT_SESSION_LIST_ERROR`
- `CHAT_SESSION_DELETE_ERROR`
- `CHAT_MESSAGE_APPEND_ERROR`
- `CHAT_MESSAGE_LIST_ERROR`
- `CHAT_MESSAGE_RECENT_ERROR`
- `CHAT_REQUEST_COMMIT_GET_ERROR`
- `CHAT_REQUEST_COMMIT_UPSERT_ERROR`

## 5. 연계 모듈

1. `src/chatbot/shared/chat/services/chat_service.py`
2. `src/chatbot/shared/chat/repositories/schemas/*.py`
3. `src/chatbot/integrations/db/*`

## 6. 변경 시 영향 범위

1. 세션/메시지 스키마 필드 변경 시 API DTO와 UI 응답 필드에 영향
2. request commit 저장 방식 변경 시 멱등 저장 보장이 깨질 수 있음
3. 정렬/페이지네이션 변경 시 세션 목록 및 히스토리 표시 순서가 바뀜
