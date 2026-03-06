# `repositories/schemas/request_commit_schema.py` 레퍼런스

## 1. 모듈 목적

`request_id` 기반 저장 멱등성을 위한 커밋 컬렉션 스키마를 생성한다.

## 2. 핵심 함수

1. `build_chat_request_commit_schema()`
- 컬렉션 이름: `CHAT_REQUEST_COMMIT_COLLECTION`
- PK: `request_id`

## 3. 컬럼 정의

1. `request_id` (`TEXT`, primary)
2. `session_id` (`TEXT`)
3. `message_id` (`TEXT`)
4. `created_at` (`TEXT`)

## 4. 실패 경로

명시적 예외를 직접 던지지 않는다.

## 5. 연계 모듈

1. `repositories/history_repository.py`
2. `services/chat_service.py`
3. `services/service_executor.py`

## 6. 변경 시 영향 범위

요청 커밋 키 구조가 바뀌면 중복 응답 저장 방지 로직(`persist_assistant_message`)의 정합성이 깨질 수 있다.
