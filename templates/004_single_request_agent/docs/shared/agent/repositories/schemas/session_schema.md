# Session Schema

## 개요

`src/single_request_agent/shared/agent/repositories/schemas/session_schema.py` 구현을 기준으로 현재 동작을 정리한다.

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

## 관련 문서

- `docs/shared/agent/repositories/history_repository.md`
