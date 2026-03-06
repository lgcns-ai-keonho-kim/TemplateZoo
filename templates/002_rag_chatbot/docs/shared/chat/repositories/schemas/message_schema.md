# Chat Message Schema

이 문서는 `src/rag_chatbot/shared/chat/repositories/schemas/message_schema.py`를 설명한다.

## 1. 목적

- 메시지 컬렉션 스키마(`CHAT_MESSAGE_COLLECTION`)를 생성한다.

## 2. 스키마 정의

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `message_id` | `TEXT` | 기본키 |
| `session_id` | `TEXT` | 세션 식별자 |
| `role` | `TEXT` | `user`/`assistant` |
| `content` | `TEXT` | 본문 |
| `sequence` | `INTEGER` | 세션 내 순번 |
| `created_at` | `TEXT` | 생성 시각 |
| `metadata` | `TEXT` | 부가 메타데이터(JSON 문자열) |

## 3. 노출 함수

- `build_chat_message_schema() -> CollectionSchema`

## 4. 관련 문서

- `docs/shared/chat/repositories/history_repository.md`
