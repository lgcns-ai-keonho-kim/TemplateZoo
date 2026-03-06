# Session Schema 문서

대상 코드: `src/plan_and_then_execute_agent/shared/chat/repositories/schemas/session_schema.py`

## 역할

세션 컬렉션 스키마를 생성합니다.

## 핵심 함수

- `build_chat_session_schema()`: `CHAT_SESSION_COLLECTION`용 스키마 반환

## 주요 컬럼

- `session_id`(PK)
- `title`
- `created_at`
- `updated_at`
- `message_count`
- `last_message_preview`

## 연관 문서

- `docs/shared/chat/repositories/history_repository.md`
