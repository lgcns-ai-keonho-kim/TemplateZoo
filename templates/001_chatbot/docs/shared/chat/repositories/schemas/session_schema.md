# `repositories/schemas/session_schema.py` 레퍼런스

이 파일은 채팅 세션 컬렉션 스키마를 만드는 팩토리다.

## 1. 코드 설명

`build_chat_session_schema()`가 반환하는 컬럼:

1. `session_id` - 기본 키
2. `title`
3. `created_at`
4. `updated_at`
5. `message_count`
6. `last_message_preview`

컬렉션 이름은 `CHAT_SESSION_COLLECTION` 상수를 사용한다.

## 2. 유지보수 포인트

1. `message_count`, `last_message_preview`는 UI 목록 표시와 최근 세션 정렬에 직접 연결된다.
2. 컬럼명을 바꾸면 `ChatHistoryMapper.session_to_document()`와 조회 매핑을 같이 수정해야 한다.

## 3. 추가 개발/확장 가이드

1. 보관 정책 필드나 pin 상태 같은 세션 메타데이터를 추가하려면 스키마, 도메인 모델, UI DTO를 함께 확장해야 한다.

## 4. 관련 코드

- `src/chatbot/shared/chat/repositories/history_repository.py`
- `src/chatbot/core/chat/models/entities.py`
