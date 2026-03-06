# Chat History Repository

이 문서는 `src/rag_chatbot/shared/chat/repositories/history_repository.py`의 영속 저장소 구현을 설명한다.

## 1. 목적

- 세션/메시지/요청 커밋을 DB에 저장/조회/삭제한다.
- `db_client` 미주입 시 SQLite 기본 엔진을 사용한다.

## 2. 초기화

초기화 입력:

1. `db_client`(선택)
2. `database_path`(기본 `CHAT_DB_PATH`)
3. `logger`(선택)

초기화 절차:

1. 세션/메시지/요청커밋 스키마 생성
2. DB 연결
3. 컬렉션 생성

## 3. 세션 API

1. `create_session`: 세션 생성 또는 기존 세션 재사용
2. `ensure_session`: session_id 기준 세션 보장
3. `get_session`: 단건 조회
4. `list_sessions`: `updated_at DESC` 정렬 조회
5. `delete_session`: 세션 + 메시지 동시 삭제

## 4. 메시지 API

1. `append_message`: 메시지 저장 + 세션 요약(`message_count`, `preview`) 갱신
2. `list_messages`: `sequence ASC` 조회
3. `get_recent_messages`: 최근 N건 조회 후 순서 복원

## 5. 요청 커밋 API

1. `is_request_committed(request_id)`: 멱등 저장 여부 조회
2. `mark_request_committed(request_id, session_id, message_id)`: 저장 완료 기록

## 6. 실패/예외 포인트

- 빈 메시지 입력: `CHAT_MESSAGE_EMPTY`
- 빈 request_id: `CHAT_REQUEST_ID_EMPTY`
- 저장소 오류: `_raise_repository_error`를 통해 `BaseAppException`으로 래핑

## 7. 관련 문서

- `docs/shared/chat/repositories/schemas/session_schema.md`
- `docs/shared/chat/repositories/schemas/message_schema.md`
- `docs/shared/chat/repositories/schemas/request_commit_schema.md`
- `docs/shared/chat/services/chat_service.md`
