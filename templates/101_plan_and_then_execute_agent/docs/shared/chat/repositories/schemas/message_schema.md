# Message Schema 문서

대상 코드: `src/plan_and_then_execute_agent/shared/chat/repositories/schemas/message_schema.py`

## 역할

메시지 컬렉션 스키마를 생성합니다.

## 핵심 함수

- `build_chat_message_schema()`: `CHAT_MESSAGE_COLLECTION`용 `CollectionSchema` 반환

## 주요 컬럼

- `message_id`(PK)
- `session_id`
- `role`
- `content`
- `sequence`
- `created_at`
- `metadata`

## 연관 문서

- `docs/shared/chat/repositories/history_repository.md`
