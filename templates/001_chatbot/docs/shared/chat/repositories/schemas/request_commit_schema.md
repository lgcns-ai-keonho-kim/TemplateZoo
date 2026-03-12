# `repositories/schemas/request_commit_schema.py` 레퍼런스

이 파일은 `request_id` 기준 멱등 저장을 위한 커밋 컬렉션 스키마를 만드는 팩토리다.

## 1. 코드 설명

`build_chat_request_commit_schema()`가 반환하는 컬럼:

1. `request_id` - 기본 키
2. `session_id`
3. `message_id`
4. `created_at`

이 스키마는 assistant 응답이 같은 `request_id`로 두 번 저장되지 않게 하는 용도로만 사용한다.

## 2. 유지보수 포인트

1. 멱등 키를 `request_id` 외 다른 값으로 바꾸면 `ServiceExecutor`와 `ChatService.persist_assistant_message()`를 함께 바꿔야 한다.
2. 이 테이블은 조회 성능보다 정합성이 중요하다. 삭제 정책을 추가할 때도 먼저 중복 저장 위험을 검토해야 한다.

## 3. 추가 개발/확장 가이드

1. 재처리 추적이나 응답 버전 관리를 붙이려면 현재 단일 커밋 구조 대신 별도 감사 로그 컬렉션을 분리하는 편이 안전하다.

## 4. 관련 코드

- `src/chatbot/shared/chat/repositories/history_repository.py`
- `src/chatbot/shared/chat/services/chat_service.py`
- `src/chatbot/shared/chat/services/service_executor.py`
