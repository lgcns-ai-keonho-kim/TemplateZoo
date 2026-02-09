# Static UI 아키텍처

이 문서는 `src/base_template/static` 정적 UI의 구조, API 연동 방식, 파일별 책임을 정의한다.

## 목적

- 브라우저 기반 Chat 화면을 제공한다.
- 단일 채팅 셀만 유지한다(가로 다중 셀 미지원).
- 우측 상단 `+` 버튼으로 새 채팅 세션을 생성한다.
- 히스토리 항목별 삭제 버튼으로 세션을 삭제한다.
- 초기 렌더링 시 세션/이력 조회를 수행한다.
- 사용자 입력을 큐 기반 Chat API에 전달하고 SSE 스트림을 소비한다.

## 연동 경계

1. 조회/삭제 API: `GET /ui-api/chat/sessions`, `GET /ui-api/chat/sessions/{session_id}/messages`, `DELETE /ui-api/chat/sessions/{session_id}`
2. 실행 API: `POST /chat/sessions`, `POST /chat/sessions/{session_id}/queue`
3. 스트림/결과 API: `GET /chat/sessions/{session_id}/tasks/{task_id}/stream`, `GET /chat/sessions/{session_id}/tasks/{task_id}/result`

UI는 `api/ui`와 `api/chat`만 호출하며 `core/*`, `integrations/*`를 직접 참조하지 않는다.

## 디렉토리 구조

```text
src/base_template/static/
  index.html
  css/
    main.css
  js/
    core/
      app.js
    ui/
      grid_manager.js
      panel_toggle.js
      theme.js
    chat/
      api_transport.js
      chat_presenter.js
      chat_cell.js
    utils/
      dom.js
      markdown.js
      syntax_highlighting/*
  asset/
    icons/*
    logo.png
```

## 파일 책임

| 파일 | 책임 |
| --- | --- |
| `src/base_template/static/index.html` | UI 루트 레이아웃과 스크립트 로딩 |
| `src/base_template/static/js/core/app.js` | 전역 앱 초기화, 히스토리 패널 상태 |
| `src/base_template/static/js/ui/grid_manager.js` | 단일 채팅 셀 생성/복원, 세션 부트스트랩 |
| `src/base_template/static/js/chat/api_transport.js` | HTTP/SSE API 호출 어댑터 |
| `src/base_template/static/js/chat/chat_presenter.js` | 메시지/상태 렌더링 보조 함수 |
| `src/base_template/static/js/chat/chat_cell.js` | 메시지 입력/전송, 스트림 소비, 상태 표시 |
| `src/base_template/static/js/utils/markdown.js` | 마크다운 렌더링 |
| `src/base_template/static/js/utils/dom.js` | DOM 유틸 |

## 부트스트랩 시퀀스

1. 브라우저가 `/ui`를 열면 `index.html`을 로드한다.
2. `App.app.bootstrap()`이 `theme`, `panelToggle`, `grid`를 초기화한다.
3. `grid_manager`가 `/ui-api/chat/sessions`를 호출해 세션 히스토리를 초기화한다.
4. 최신 세션 1개를 활성화하고 `/ui-api/chat/sessions/{session_id}/messages`로 이력을 렌더링한다.
5. 세션이 없으면 `/chat/sessions`로 신규 세션 1개를 생성해 활성화한다.
6. 사용자가 `+` 버튼을 누르면 `/chat/sessions`로 신규 세션을 만들고 즉시 활성 세션으로 전환한다.
7. 사용자가 히스토리 항목의 삭제 버튼을 누르면 `/ui-api/chat/sessions/{session_id}`로 세션과 이력을 삭제한다.

## 메시지 전송 시퀀스

1. 사용자가 메시지를 입력하면 `chat_cell`이 `/chat/sessions/{session_id}/queue`를 호출한다.
2. 응답으로 받은 `task_id`로 `/chat/sessions/{session_id}/tasks/{task_id}/stream` SSE를 연결한다.
3. `type=token` 이벤트를 누적해 메시지 버블을 갱신한다.
4. `type=done` 수신 시 `done` payload의 최종 텍스트를 우선 사용하고, 값이 비어 있을 때만 `/chat/sessions/{session_id}/tasks/{task_id}/result` 조회로 확정한다.
5. 히스토리 패널 프리뷰를 최신 응답 기준으로 갱신한다.
6. 히스토리 항목 클릭 시 동일 단일 셀에서 해당 세션으로 전환한다.

## 스크롤 정책

### 스크롤 소유권

- 세로 스크롤은 `.chat-cell__messages`만 담당한다.
- 상위 컨테이너(`body`, `.app-body`, `.chat-grid`, `.chat-cell`)는 레이아웃 할당만 담당한다.

### 자동 스크롤 상태

1. `FOLLOWING`: 하단 근처에서 스트리밍 토큰 수신 시 자동 하단 추적
2. `PAUSED_BY_USER`: 사용자가 위로 스크롤한 상태, 자동 추적 중단
3. 하단 근처로 복귀하면 `FOLLOWING` 자동 전환

### 스트리밍 렌더 정책

1. 스트림 수신 버퍼(`received`)와 화면 표시 버퍼(`visible`)를 분리해 서버 chunk 크기와 UI 표시 속도를 분리한다.
2. 타입라이터 루프는 `requestAnimationFrame` 기반으로 문자 단위 노출을 진행하고, 매 프레임 마크다운/문법 강조를 즉시 반영한다.
3. `done` 이벤트에서 최종 렌더를 1회 확정한다.
4. 최종 렌더 시 하단 보정 스크롤을 다중 프레임으로 수행한다.

## 세션 삭제 시퀀스

1. 사용자가 히스토리 항목의 삭제 버튼을 누르면 확인 대화상자를 표시한다.
2. 확인 시 `api_transport`가 `DELETE /ui-api/chat/sessions/{session_id}`를 호출한다.
3. 성공하면 히스토리 항목을 제거한다.
4. 삭제 대상이 활성 세션이면 다음 세션을 활성화하고, 남은 세션이 없으면 신규 세션을 자동 생성한다.

## 오류 처리 기준

- 네트워크/HTTP 오류는 셀 상태를 `실패`로 전환한다.
- SSE 연결 오류는 일정 시간 자동 복구를 시도하고, 복구 실패 시 상태 조회 후 재연결 또는 실패 처리한다.
- 큐 등록 실패 시 어시스턴트 플레이스홀더에 오류 문구를 표시한다.
- 마크다운 렌더링 시 입력 HTML은 이스케이프 처리한다.

## 트러블슈팅

1. 스크롤이 멈춘 것처럼 보이면 강력 새로고침(`Ctrl+Shift+R`)으로 정적 리소스 캐시를 먼저 비운다.
2. 개발자도구에서 `.chat-cell__messages`가 실제 스크롤 컨테이너인지 확인한다.
3. 장문 응답에서 느려지면 스트리밍 중간 렌더 주기와 최종 렌더 타이밍을 점검한다.
4. 세션 전환 직후 하단 위치가 어긋나면 활성 셀 재생성 시점의 초기 스크롤 로직을 점검한다.

## 구현 규칙

1. 정적 UI 모듈은 IIFE 패턴과 `window.App.*` 네임스페이스를 유지한다.
2. API 경로는 `api_transport.js`에만 정의한다.
3. `chat_cell.js`는 전송 세부사항을 직접 구현하지 않고 transport 함수를 호출한다.
4. UI 상태(stage/pill/text)는 `chat_cell.js`의 단일 상태 머신으로 관리한다.
5. 채팅 셀은 단일 인스턴스로 유지하며, 다중 셀 생성/확장/닫기 기능을 제공하지 않는다.
