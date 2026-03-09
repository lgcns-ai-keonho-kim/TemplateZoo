# repositories/schemas/request_commit_schema.py

request 커밋(멱등성 기록) 컬렉션 스키마를 생성한다.

## 1. 공개 함수

| 함수 | 설명 |
| --- | --- |
| `build_chat_request_commit_schema()` | request_id 기준 커밋 컬렉션 정의 반환 |

## 2. 컬럼 정의

- primary key: `request_id`
- 일반 컬럼: `session_id`, `message_id`, `created_at`

## 3. 연관 모듈

- `repositories/history_repository.py`
- `services/chat_service.py`
