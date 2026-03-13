# build_chat_message_schema 가이드

이 문서는 `src/rag_chatbot/shared/chat/repositories/schemas/message_schema.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

Chat 저장소가 사용할 컬렉션 스키마를 생성하는 팩토리 함수다.

## 2. 공개 구성

- 함수 `build_chat_message_schema`

## 3. 코드 설명

- 정의된 컬럼: `message_id`, `session_id`, `role`, `content`, `sequence`, `created_at`, `metadata`

## 4. 유지보수/추가개발 포인트

- 컬럼을 추가하면 mapper, 저장소 query, API DTO까지 함께 점검해야 실제 응답에 반영된다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
