# Chat Service

이 문서는 `src/rag_chatbot/shared/chat/services/chat_service.py`의 도메인 실행 서비스를 설명한다.

## 1. 목적

- 세션/메시지 저장소와 그래프 실행을 결합한다.
- 동기/비동기 실행, 스트리밍, 멱등 저장을 제공한다.

## 2. 주요 의존성

| 의존성 | 역할 |
| --- | --- |
| `GraphPort` | 그래프 invoke/stream 실행 |
| `ChatHistoryRepository` | 세션/메시지/커밋 저장 |
| `ChatSessionMemoryStore` | 문맥 메시지 캐시 |

## 3. 세션/메시지 API

1. `create_session`, `list_sessions`, `get_session`, `list_messages`, `delete_session`
2. `append_assistant_message`: assistant 메시지 저장 + 메모리 반영
3. `_append_user_message_existing_session`: user 메시지 저장 + 메모리 반영

세션 삭제 시 `repository.delete_session`과 `memory_store.clear_session`을 함께 수행한다.

## 4. 실행 API

1. `invoke`, `ainvoke`: 최종 텍스트를 즉시 반환
2. `stream`, `astream`: 이벤트 스트림 반환

스트림 종료 규칙:

1. 그래프 `token` 이벤트를 누적한다.
2. 토큰이 비어 있으면 `assistant_message`를 fallback으로 사용한다.
3. 최종적으로 `references` 이벤트와 `done` 이벤트를 생성한다.
4. 최종 본문이 비어 있으면 `CHAT_STREAM_EMPTY` 예외를 발생시킨다.

## 5. 문맥 생성 규칙

- `_build_context_history`는 `context_window`를 최소 1로 보정한다.
- 현재 요청 메시지는 `exclude_message_id`로 제외한다.
- `max_sequence`를 넘어서는 메시지는 문맥에서 제외한다.
- 세션 캐시가 없으면 `_ensure_memory_loaded`로 저장소 최근 메시지를 로드한다.

## 6. 멱등 저장 규칙

`persist_assistant_message`:

1. `is_request_committed`로 선조회
2. 미커밋일 때만 assistant 저장
3. 저장 후 `mark_request_committed` 기록

중복 done 또는 재시도 상황에서도 assistant 중복 저장을 방지한다.

## 7. 실패/예외 포인트

- 세션 미존재: `CHAT_SESSION_NOT_FOUND`
- 빈 메시지 입력: `CHAT_MESSAGE_EMPTY`
- 빈 스트림 본문: `CHAT_STREAM_EMPTY`

## 8. 관련 문서

- `docs/shared/chat/interface/ports.md`
- `docs/shared/chat/repositories/history_repository.md`
- `docs/shared/chat/memory/session_store.md`
- `docs/shared/chat/services/service_executor.md`
