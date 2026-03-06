# `repositories/schemas/session_schema.py` 레퍼런스

## 1. 모듈 목적

Chat 세션 컬렉션 스키마(`CollectionSchema`)를 생성한다.

## 2. 핵심 함수

1. `build_chat_session_schema()`
- 컬렉션 이름: `CHAT_SESSION_COLLECTION`
- PK: `session_id`

## 3. 컬럼 정의

1. `session_id` (`TEXT`, primary)
2. `title` (`TEXT`)
3. `created_at` (`TEXT`)
4. `updated_at` (`TEXT`)
5. `message_count` (`INTEGER`)
6. `last_message_preview` (`TEXT`)

## 4. 실패 경로

명시적 예외를 직접 던지지 않는다.

## 5. 연계 모듈

1. `repositories/history_repository.py`

## 6. 변경 시 영향 범위

컬럼 변경 시 `ChatHistoryMapper`와 UI 세션 응답 스펙을 함께 갱신해야 한다.
