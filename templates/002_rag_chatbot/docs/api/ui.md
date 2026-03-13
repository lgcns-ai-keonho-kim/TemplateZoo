# UI API

## 엔드포인트

- `POST /ui-api/chat/sessions`
  - 요청: `title?`
  - 응답: `session_id`
- `GET /ui-api/chat/sessions`
  - 응답: `sessions`, `limit`, `offset`
- `GET /ui-api/chat/sessions/{session_id}/messages`
  - 응답: `session_id`, `messages`, `limit`, `offset`
- `DELETE /ui-api/chat/sessions/{session_id}`
  - 응답: `session_id`, `deleted=true`

## DTO

- 세션 요약: `session_id`, `title`, `updated_at`, `message_count`, `last_message_preview`
- 메시지 항목: `message_id`, `role`, `content`, `sequence`, `created_at`

## 페이지네이션

- 서버 기본값: `DEFAULT_PAGE_SIZE=50`, `MAX_PAGE_SIZE=200`
- 프런트 기본값: `listSessions(limit=20)`, `listMessages(limit=200)`
- 프런트 기본값과 서버 기본값은 다르다.

## 의존 경로

- 라우터: `src/rag_chatbot/api/ui/routers/*.py`
- 서비스: `src/rag_chatbot/api/ui/services/chat_service.py`
- 프런트 호출: `src/rag_chatbot/static/js/chat/api_transport.js`
