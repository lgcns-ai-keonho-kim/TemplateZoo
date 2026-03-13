# API UI 가이드

이 문서는 `src/rag_chatbot/api/ui` 계층이 정적 UI에 제공하는 세션/메시지 조회 API를 설명한다.

## 1. 현재 엔드포인트

- `POST /ui-api/chat/sessions`: 제목이 있으면 반영해 세션을 생성한다.
- `GET /ui-api/chat/sessions`: 세션 목록을 반환한다.
- `GET /ui-api/chat/sessions/{session_id}/messages`: 세션 메시지 목록을 반환한다.
- `DELETE /ui-api/chat/sessions/{session_id}`: 세션과 메시지를 함께 삭제한다.

## 2. 페이지네이션 기준

- 서버 기본값은 `core/chat/const/settings.py` 기준 `DEFAULT_PAGE_SIZE=50`, `MAX_PAGE_SIZE=200`이다.
- 정적 UI 호출 기본값은 `static/js/chat/api_transport.js` 기준 `listSessions(limit=20)`, `listMessages(limit=200)`다.
- 서버 기본값과 프런트 기본값은 다르므로 문서와 구현에서 분리해서 봐야 한다.

## 3. 현재 DTO

- 세션 요약: `session_id`, `title`, `updated_at`, `message_count`, `last_message_preview`
- 메시지 항목: `message_id`, `role`, `content`, `sequence`, `created_at`
- 삭제 응답: `session_id`, `deleted=true`

## 4. 유지보수/추가개발 포인트

- UI 응답 포맷을 바꾸면 `api/ui/models`, `api/ui/utils/mappers.py`, `static/js/ui/grid_manager.js`, `static/js/chat/chat_cell.js`를 함께 봐야 한다.
- 목록 기본값을 바꾸면 서버 `Query` 제약과 프런트 퍼사드 기본값이 서로 어긋나지 않는지 확인해야 한다.
- UI 계층은 자체 저장소를 만들지 않으므로, 데이터 규칙 변경은 `ChatService`와 repository까지 추적하는 편이 안전하다.

## 5. 관련 문서

- `docs/api/overview.md`
- `docs/shared/chat/README.md`
- `docs/static/ui.md`
