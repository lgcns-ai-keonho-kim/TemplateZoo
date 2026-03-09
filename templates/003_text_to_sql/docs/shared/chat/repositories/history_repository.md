# repositories/history_repository.py

세션/메시지/요청 커밋을 영속화하는 저장소 구현체다.

## 1. 역할

- `DBClient`를 통해 chat 컬렉션 3종을 관리한다.
- `request_id` 커밋 테이블로 assistant 저장 멱등성을 지원한다.
- `db_client` 미주입 시 SQLite 엔진을 기본 생성한다.

## 2. 주요 메서드

| 메서드 | 설명 |
| --- | --- |
| `create_session`, `ensure_session` | 세션 생성/보장 |
| `append_message` | 메시지 저장 + 세션 요약 갱신 |
| `is_request_committed`, `mark_request_committed` | request_id 커밋 조회/기록 |
| `list_messages`, `get_recent_messages` | 메시지 조회 |
| `delete_session` | 세션과 메시지 동시 삭제 |

## 3. 실패/예외

| 코드 | 발생 조건 |
| --- | --- |
| `CHAT_MESSAGE_EMPTY` | 저장할 메시지 본문이 비어 있음 |
| `CHAT_REQUEST_ID_EMPTY` | 커밋 조회/기록 시 request_id가 비어 있음 |
| `CHAT_*_ERROR` | 저장소 내부 예외를 `_raise_repository_error`에서 래핑 |

## 4. 스키마 의존

- 세션: `repositories/schemas/session_schema.py`
- 메시지: `repositories/schemas/message_schema.py`
- 요청 커밋: `repositories/schemas/request_commit_schema.py`
