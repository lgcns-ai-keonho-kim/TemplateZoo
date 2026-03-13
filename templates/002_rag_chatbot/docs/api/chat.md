# Chat API

## 엔드포인트

- `POST /chat`
  - 요청: `session_id?`, `message`, `context_window(1..100)`
  - 응답: `202`, `session_id`, `request_id`, `status=QUEUED`
  - `session_id`가 비어 있으면 새 세션을 만든다.
- `GET /chat/{session_id}`
  - 응답: `session_id`, `messages`, `last_status`, `updated_at`
  - 실행 이력이 없으면 `last_status`는 `IDLE`일 수 있다.
- `GET /chat/{session_id}/events?request_id=...`
  - 응답 형식: `text/event-stream`
  - 요청 단위 스트림만 반환한다.

## SSE 계약

- 이벤트 타입: `start`, `token`, `references`, `done`, `error`
- 공개 페이로드 필드: `session_id`, `request_id`, `type`, `node`, `content`, `status`, `error_message`, `metadata?`
- `metadata`는 선택 필드다.
- `done`이면 `status=COMPLETED`, `error`이면 `status=FAILED`가 설정된다.
- 실제 공개 이벤트 정규화는 `ServiceExecutor`가 수행한다.

## 상태 코드 매핑

- `CHAT_SESSION_NOT_FOUND` -> `404`
- `CHAT_MESSAGE_EMPTY`, `CHAT_STREAM_NODE_INVALID` -> `400`
- `CHAT_JOB_QUEUE_FAILED` -> `503`
- `CHAT_STREAM_TIMEOUT` -> `504`
- 그 외 도메인 예외 -> `500`

## 관련 코드

- 라우터: `src/rag_chatbot/api/chat/routers/*.py`
- 모델: `src/rag_chatbot/api/chat/models/*.py`
- 실행기: `src/rag_chatbot/shared/chat/services/service_executor.py`
