# API Chat 가이드

이 문서는 `src/rag_chatbot/api/chat`이 제공하는 HTTP 계약과 SSE 흐름, 확장 시 주의할 지점을 정리한다.

## 1. 요청/응답 모델

- `SubmitChatRequest`: `session_id?`, `message`, `context_window(1..100)`
- `SubmitChatResponse`: `session_id`, `request_id`, `status=QUEUED`
- `SessionSnapshotResponse`: `session_id`, `messages`, `last_status`, `updated_at`
- `StreamPayload`: `session_id`, `request_id`, `type`, `node`, `content`, `status`, `error_message`, `metadata`

## 2. 현재 엔드포인트

- `POST /chat`: 작업을 큐에 적재하고 즉시 `202`를 반환한다.
- `GET /chat/{session_id}/events?request_id=...`: `text/event-stream`으로 요청 단위 이벤트를 구독한다.
- `GET /chat/{session_id}`: 메시지 목록과 최근 세션 상태를 함께 조회한다.

## 3. SSE 이벤트 계약

- 이벤트 타입은 `start`, `token`, `references`, `done`, `error` 다섯 가지다.
- `done`이면 `status=COMPLETED`, `error`이면 `status=FAILED`가 설정된다.
- `metadata`는 참고자료, 토큰 수 같은 부가 정보를 전달하는 공개 필드다.
- 실제 공개 이벤트 정규화는 `ServiceExecutor`가 수행한다.

## 4. 예외와 상태 코드

- `CHAT_SESSION_NOT_FOUND` -> `404`
- `CHAT_MESSAGE_EMPTY`, `CHAT_STREAM_NODE_INVALID` -> `400`
- `CHAT_JOB_QUEUE_FAILED` -> `503`
- `CHAT_STREAM_TIMEOUT` -> `504`
- 그 외 도메인 예외 -> `500`

## 5. 유지보수/추가개발 포인트

- 요청 필드를 늘릴 때는 DTO, 라우터, `ServiceExecutor.submit_job()` payload, 프런트 호출부를 동시에 수정해야 한다.
- 새 이벤트 타입을 추가할 때는 `StreamPayload`, `ServiceExecutor`, `docs/static/ui.md`, 프런트 이벤트 파서를 함께 갱신해야 한다.
- 세션 스냅샷 정책을 바꾸면 `ChatService`와 UI 메시지 로딩 정책이 어긋나지 않는지 확인해야 한다.

## 6. 관련 문서

- `docs/api/overview.md`
- `docs/api/ui.md`
- `docs/core/chat.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/static/ui.md`
