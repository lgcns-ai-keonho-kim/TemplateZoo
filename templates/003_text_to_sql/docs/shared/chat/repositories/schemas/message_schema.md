# repositories/schemas/message_schema.py

메시지 컬렉션 스키마를 생성하는 팩토리 함수 모듈이다.

## 1. 공개 함수

| 함수 | 설명 |
| --- | --- |
| `build_chat_message_schema()` | chat 메시지 저장 컬렉션 정의 반환 |

## 2. 컬럼 정의

- primary key: `message_id`
- 일반 컬럼: `session_id`, `role`, `content`, `sequence`, `created_at`, `metadata`

## 3. 관련 코드

- `repositories/history_repository.py`
- `src/text_to_sql/integrations/db/base/models.py`
