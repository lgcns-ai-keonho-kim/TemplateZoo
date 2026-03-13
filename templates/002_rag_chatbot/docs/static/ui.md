# Static UI 가이드

이 문서는 `src/rag_chatbot/static`의 현재 구조와 상태 흐름, 유지보수 포인트를 코드 기준으로 정리한다.

## 1. 현재 구조

- 엔트리: `index.html`
- 초기화 퍼사드: `js/core/app.js`
- 세션/셀 관리: `js/ui/grid_manager.js`, `js/ui/grid/helpers.js`
- 패널/테마: `js/ui/panel_toggle.js`, `js/ui/theme.js`
- API 퍼사드: `js/chat/api_transport.js`
- HTTP/SSE 전송: `js/chat/transport/http.js`, `js/chat/transport/stream.js`
- 채팅 셀: `js/chat/chat_cell.js`, `js/chat/cell/*.js`
- 표현 계층: `js/chat/chat_presenter.js`
- 유틸: `js/utils/*`

## 2. 현재 동작 흐름

1. `bootstrap()`이 theme, panel toggle, grid 초기화를 순서대로 수행한다.
2. `grid_manager`가 세션 목록을 불러오고 활성 셀을 하나만 유지한다.
3. 메시지 전송은 `POST /chat` 후 `request_id`를 받고, 1초 대기 뒤 SSE를 연결한다.
4. `token` 이벤트는 `node === "response"`일 때만 본문 버퍼에 누적한다.
5. `references`는 `type=references` 또는 `done.metadata.references` fallback으로 렌더한다.

## 3. 현재 상태 포인트

- 전역 grid 상태: `activeSessionId`, `activeCell`, `sessionMeta`, `isLoading`
- 개별 채팅 상태: `sessionId`, `activeRequestId`, `isSending`, `finalized`, `streamHandle`, `tokenBuffer`, `receivedText`, `references`, `scrollMode`, `destroyed`, `timers`
- 세션 전환 시 기존 셀의 `destroy()`를 먼저 호출한다.

## 4. 유지보수/추가개발 포인트

- 번들러가 없어서 script 로드 순서가 계약이다. 의존 모듈이 먼저 로드되지 않으면 즉시 예외가 난다.
- SSE payload를 바꾸면 `transport/stream.js`, `chat/cell/stream.js`, `chat_presenter.js`를 함께 수정해야 한다.
- reference 포맷이 바뀌면 `reference_parser.js`를 확장 지점으로 보는 것이 현재 구조와 맞다.
- 세션 전환 시 `destroy()`를 빼먹으면 이벤트 리스너와 타이머가 누수된다.

## 5. 관련 문서

- `docs/api/chat.md`
- `docs/api/ui.md`
- `docs/shared/chat/services/service_executor.md`
