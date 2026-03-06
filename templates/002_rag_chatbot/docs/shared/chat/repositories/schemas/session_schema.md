# Chat Session Schema

이 문서는 `src/rag_chatbot/shared/chat/repositories/schemas/session_schema.py`를 설명한다.

## 1. 목적

- 세션 컬렉션 스키마(`CHAT_SESSION_COLLECTION`)를 생성한다.

## 2. 스키마 정의

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `TEXT` | 기본키 |
| `title` | `TEXT` | 세션 제목 |
| `created_at` | `TEXT` | 생성 시각 |
| `updated_at` | `TEXT` | 마지막 갱신 시각 |
| `message_count` | `INTEGER` | 메시지 수 |
| `last_message_preview` | `TEXT` | 마지막 메시지 미리보기 |

## 3. 노출 함수

- `build_chat_session_schema() -> CollectionSchema`

## 4. 관련 문서

- `docs/shared/chat/repositories/history_repository.md`
