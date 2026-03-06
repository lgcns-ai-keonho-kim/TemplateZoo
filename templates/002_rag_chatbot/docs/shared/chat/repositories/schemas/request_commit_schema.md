# Chat Request Commit Schema

이 문서는 `src/rag_chatbot/shared/chat/repositories/schemas/request_commit_schema.py`를 설명한다.

## 1. 목적

- 요청 단위 멱등 저장 추적 컬렉션(`CHAT_REQUEST_COMMIT_COLLECTION`) 스키마를 생성한다.

## 2. 스키마 정의

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `request_id` | `TEXT` | 기본키 |
| `session_id` | `TEXT` | 세션 식별자 |
| `message_id` | `TEXT` | 저장된 assistant 메시지 ID |
| `created_at` | `TEXT` | 커밋 시각 |

## 3. 노출 함수

- `build_chat_request_commit_schema() -> CollectionSchema`

## 4. 관련 문서

- `docs/shared/chat/repositories/history_repository.md`
- `docs/shared/chat/services/chat_service.md`
