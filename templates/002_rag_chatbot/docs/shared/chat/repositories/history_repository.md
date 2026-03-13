# ChatHistoryRepository 가이드

이 문서는 `src/rag_chatbot/shared/chat/repositories/history_repository.py`의 현재 구현을 기준으로 역할과 유지보수 포인트를 정리한다.

## 1. 역할

대화 세션, 메시지, request_id 멱등 커밋을 함께 관리하는 저장소다.

## 2. 공개 구성

- 클래스 `ChatHistoryRepository`
  공개 메서드: `close`, `create_session`, `ensure_session`, `get_session`, `list_sessions`, `append_message`, `is_request_committed`, `mark_request_committed`, `list_messages`, `get_recent_messages`, `delete_session`

## 3. 코드 설명

- 기본 생성 경로에서는 SQLiteEngine을 직접 만들고, 외부 `DBClient` 주입 시 그 엔진을 그대로 사용한다.
- 세션 요약 정보는 메시지 추가 시 함께 갱신된다.
- `request_id` 저장 여부는 별도 컬렉션으로 관리한다.

## 4. 유지보수/추가개발 포인트

- 세션/메시지 스키마를 바꾸면 mapper와 schema 팩토리, list/query 정렬 조건을 함께 수정해야 한다.
- 멱등 저장 규칙을 바꿀 때는 `mark_request_committed`와 `is_request_committed`의 의미를 먼저 고정해야 한다.

## 5. 관련 문서

- `docs/shared/overview.md`
- `docs/shared/chat/README.md`
