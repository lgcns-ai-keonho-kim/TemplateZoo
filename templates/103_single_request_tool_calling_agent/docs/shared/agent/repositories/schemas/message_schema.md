# Message Schema

## 개요

`src/single_request_tool_agent/shared/agent/repositories/schemas/message_schema.py` 구현을 기준으로 현재 동작을 정리한다.

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

## 관련 문서

- `docs/shared/agent/repositories/history_repository.md`
