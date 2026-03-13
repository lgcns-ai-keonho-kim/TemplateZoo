# API UI 레퍼런스

이 문서는 `src/chatbot/api/ui`의 세션/메시지 조회 및 관리 API를 정리한다.

## 1. 역할

UI API는 정적 프런트엔드가 직접 호출하는 관리 경로다.

현재 책임:

1. 세션 생성
2. 세션 목록 조회
3. 세션별 메시지 목록 조회
4. 세션 삭제

채팅 실행 자체는 하지 않으며, 실행은 `/chat` 계열 API가 담당한다.

## 2. 구성 요소

```text
src/chatbot/api/ui/
  models/
    session.py
    message.py
  routers/
    create_session.py
    list_sessions.py
    list_messages.py
    delete_session.py
    common.py
    router.py
  services/
    __init__.py
    chat_service.py
  utils/
    mappers.py
```

호출 흐름:

```text
UI Router
 -> ChatUIService
 -> ChatService
 -> ChatHistoryRepository
 -> UI DTO
```

## 3. 엔드포인트

### 3-1. `POST /ui-api/chat/sessions`

- 상태코드: `201 Created`
- 요청 모델: `UICreateSessionRequest`
- 응답 모델: `UICreateSessionResponse`

규칙:

1. 제목이 없으면 저장소 기본 제목 `"새 대화"`가 적용된다.
2. 응답은 `session_id`만 반환한다.

### 3-2. `GET /ui-api/chat/sessions`

- 상태코드: `200 OK`
- 응답 모델: `UISessionListResponse`
- Query:
  - `limit`: 기본값 `50`, 최소 `1`, 최대 `200`
  - `offset`: 기본값 `0`, 최소 `0`

특징:

1. 저장소 정렬 기준은 `updated_at DESC`다.
2. 응답의 `limit`, `offset`은 요청 값을 그대로 반영한다.

### 3-3. `GET /ui-api/chat/sessions/{session_id}/messages`

- 상태코드: `200 OK`
- 응답 모델: `UIMessageListResponse`
- Query:
  - `limit`: 기본값 `50`, 최소 `1`, 최대 `200`
  - `offset`: 기본값 `0`, 최소 `0`

특징:

1. 세션이 없으면 `CHAT_SESSION_NOT_FOUND`로 `404`를 반환한다.
2. 메시지는 저장소 기준 `sequence ASC` 순서다.

### 3-4. `DELETE /ui-api/chat/sessions/{session_id}`

- 상태코드: `200 OK`
- 응답 모델: `UIDeleteSessionResponse`

특징:

1. 세션과 세션 소속 메시지를 삭제한다.
2. 세션이 없으면 `404`를 반환한다.
3. 삭제 성공 시 `{ "session_id": "...", "deleted": true }`를 반환한다.

## 4. 정적 UI와의 관계

실제 브라우저 호출값과 API 기본값은 다르다.

1. API 기본 페이지 크기: `50`
2. `grid_manager.js` 초기 세션 목록 호출: `listSessions(50, 0)`
3. `api_transport.listSessions()` 내부 fallback: `20`
4. `grid_manager.js` 메시지 조회 호출: `listMessages(sessionId, 200, 0)`
5. `api_transport.listMessages()` 내부 fallback: `200`

즉, API 기본값과 프런트 기본값을 문서에서 구분해서 적어야 한다.

## 5. 유지보수 포인트

1. `ChatUIService`는 표현 전용 서비스이므로 저장소 분기나 HTTP 예외 생성을 넣지 않는다.
2. `to_ui_session`, `to_ui_message`는 순수 매퍼다.
3. 세션/메시지 응답 형식이 바뀌면 정적 UI 히스토리 패널과 채팅 셀 렌더링이 함께 영향을 받는다.
4. `limit`, `offset` 정책을 바꾸면 API와 브라우저 호출값을 동시에 확인해야 한다.

## 6. 관련 문서

- `docs/api/overview.md`
- `docs/api/chat.md`
- `docs/static/ui.md`
