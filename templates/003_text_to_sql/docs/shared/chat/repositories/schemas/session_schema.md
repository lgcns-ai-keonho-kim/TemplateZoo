# repositories/schemas/session_schema.py

세션 컬렉션 스키마를 생성하는 팩토리 함수 모듈이다.

## 1. 공개 함수

| 함수 | 설명 |
| --- | --- |
| `build_chat_session_schema()` | chat 세션 저장 컬렉션 정의 반환 |

## 2. 컬럼 정의

- primary key: `session_id`
- 일반 컬럼: `title`, `created_at`, `updated_at`, `message_count`, `last_message_preview`

## 3. 연관 모듈

- `repositories/history_repository.py`
- `src/text_to_sql/core/chat/models/entities.py`
