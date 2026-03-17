# Request Commit Schema

## 개요

`src/single_request_agent/shared/agent/repositories/schemas/request_commit_schema.py` 구현을 기준으로 현재 동작을 정리한다.

request_id 기반 저장 멱등성 기록 스키마를 생성합니다.

## 핵심 함수

- `build_chat_request_commit_schema()`: `CHAT_REQUEST_COMMIT_COLLECTION`용 스키마 반환

## 주요 컬럼

- `request_id`(PK)
- `session_id`
- `message_id`
- `created_at`

## 관련 문서

- `docs/shared/agent/repositories/history_repository.md`
