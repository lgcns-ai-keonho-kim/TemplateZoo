# `repositories/schemas/message_schema.py` 레퍼런스

## 1. 모듈 목적

Chat 메시지 컬렉션 스키마(`CollectionSchema`)를 생성한다.

## 2. 핵심 함수

1. `build_chat_message_schema()`
- 컬렉션 이름: `CHAT_MESSAGE_COLLECTION`
- PK: `message_id`

## 3. 컬럼 정의

1. `message_id` (`TEXT`, primary)
2. `session_id` (`TEXT`)
3. `role` (`TEXT`)
4. `content` (`TEXT`)
5. `sequence` (`INTEGER`)
6. `created_at` (`TEXT`)
7. `metadata` (`TEXT`)

## 4. 실패 경로

명시적 예외를 직접 던지지 않는다.

## 5. 연계 모듈

1. `repositories/history_repository.py`

## 6. 변경 시 영향 범위

`metadata`/`sequence` 정책 변경 시 메시지 정렬과 진단 정보 저장 방식이 달라진다.
