# API UI 레퍼런스

이 문서는 `src/chatbot/api/ui`의 세션/메시지 조회 API를 코드 기준으로 정리한다.

## 1. 역할

UI API는 정적 프런트엔드가 직접 사용하는 조회/관리 경로다. 현재 책임은 다음과 같다.

1. 세션 생성
2. 세션 목록 조회
3. 세션별 메시지 목록 조회
4. 세션 삭제

실제 채팅 실행은 담당하지 않으며, 그 역할은 `/chat` 계열 API가 가진다.

## 2. 디렉터리 구조

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

| 경로 | 코드 설명 | 유지보수 포인트 |
| --- | --- | --- |
| `models/session.py` | 세션 생성/목록/삭제 응답 DTO | 세션 필드 확장 시 정적 UI 소비 필드와 함께 관리한다 |
| `models/message.py` | 메시지 목록 DTO | 메시지 필드가 늘어나면 UI 렌더링 방식도 확인한다 |
| `routers/*.py` | HTTP 파라미터 검증과 서비스 호출 | 저장소나 코어 로직을 직접 호출하지 않는다 |
| `services/chat_service.py` | `ChatService` 결과를 UI DTO로 변환 | UI 전용 표현 변환만 맡고 비즈니스 규칙은 넣지 않는다 |
| `utils/mappers.py` | 순수 DTO 매핑 함수 | 포맷 변경 시 서비스보다 매퍼를 먼저 수정한다 |

## 3. 엔드포인트

### 3-1. `POST /ui-api/chat/sessions`

- 상태코드: `201 Created`
- 요청 모델: `UICreateSessionRequest`
- 응답 모델: `UICreateSessionResponse`

요청 예시:

```json
{
  "title": "새 대화"
}
```

응답 예시:

```json
{
  "session_id": "3f3b..."
}
```

설명:

1. 제목이 비어 있으면 저장소 기본 제목이 적용된다.
2. 응답은 `session_id`만 반환한다.

### 3-2. `GET /ui-api/chat/sessions`

- 상태코드: `200 OK`
- 응답 모델: `UISessionListResponse`
- Query:
  - `limit`: 기본값 `50`, 최소 `1`, 최대 `200`
  - `offset`: 기본값 `0`, 최소 `0`

응답 예시:

```json
{
  "sessions": [
    {
      "session_id": "3f3b...",
      "title": "새 대화",
      "updated_at": "2026-03-12T01:23:45.123456+00:00",
      "message_count": 3,
      "last_message_preview": "요약 미리보기"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

설명:

1. 저장소 정렬 기준은 `updated_at DESC`다.
2. 응답의 `limit`, `offset`은 요청 값을 그대로 돌려준다.

### 3-3. `GET /ui-api/chat/sessions/{session_id}/messages`

- 상태코드: `200 OK`
- 응답 모델: `UIMessageListResponse`
- Query:
  - `limit`: 기본값 `50`, 최소 `1`, 최대 `200`
  - `offset`: 기본값 `0`, 최소 `0`

응답 예시:

```json
{
  "session_id": "3f3b...",
  "messages": [
    {
      "message_id": "...",
      "role": "assistant",
      "content": "안녕하세요",
      "sequence": 2,
      "created_at": "2026-03-12T01:23:50.123456+00:00"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

설명:

1. 세션이 없으면 `CHAT_SESSION_NOT_FOUND`로 `404`를 반환한다.
2. 메시지 순서는 저장소 기준 `sequence ASC`다.

### 3-4. `DELETE /ui-api/chat/sessions/{session_id}`

- 상태코드: `200 OK`
- 응답 모델: `UIDeleteSessionResponse`

응답 예시:

```json
{
  "session_id": "3f3b...",
  "deleted": true
}
```

설명:

1. 세션과 메시지를 함께 삭제한다.
2. 세션이 없으면 `404`를 반환한다.

## 4. 실행 흐름

```text
UI Router
 -> ChatUIService
 -> ChatService
 -> ChatHistoryRepository
 -> UI DTO
```

핵심 포인트:

1. UI 서비스는 `ChatService`를 재사용한다.
2. UI DTO는 도메인 엔티티를 그대로 노출하지 않고 얇은 응답 모델로 다시 매핑한다.
3. 예외는 `BaseAppException`에서 시작해 UI 라우터 공통 함수에서 HTTP 예외로 바뀐다.

## 5. 정적 UI와의 계약

정적 UI 코드 기준 호출 방식:

1. `grid_manager.js` 부트스트랩은 `listSessions(50, 0)`을 호출한다.
2. `api_transport.listSessions()` 자체 기본값은 `20`이다.
3. `grid_manager.js` 메시지 조회는 `listMessages(sessionId, 200, 0)`을 호출한다.
4. 따라서 API 기본값과 실제 브라우저 호출값은 다를 수 있다.

문서와 유지보수 시 이 둘을 구분해서 적는 것이 안전하다.

## 6. 유지보수 포인트

1. `limit` 기본값은 API 계층에서 50이지만, 브라우저 초기 로딩은 200 메시지까지 가져올 수 있다.
2. `ChatUIService`는 표현 전용 계층이므로 여기에 저장소 분기나 HTTP 예외 생성을 넣지 않는 편이 좋다.
3. `to_ui_session`, `to_ui_message`는 순수 함수이므로 직렬화 규칙 변경 시 가장 먼저 확인해야 한다.
4. UI 세션 관련 응답 형식이 바뀌면 정적 히스토리 패널 렌더링이 함께 깨질 수 있다.

## 7. 추가 개발과 확장 가이드

### 7-1. 응답 필드 추가

1. DTO 모델에 필드를 추가한다.
2. 매퍼를 갱신한다.
3. 필요한 데이터가 없다면 `shared` 계층에서 조회를 확장한다.
4. 정적 UI가 해당 필드를 사용할지 먼저 결정한다.

### 7-2. 새로운 UI 관리 API 추가

1. `routers`에 경로를 추가한다.
2. `router.py` 집계 라우터에 등록한다.
3. 표현 변환이 필요하면 `ChatUIService`와 `utils/mappers.py`를 함께 확장한다.

### 7-3. 페이지네이션 정책 변경

1. `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE` 영향을 함께 본다.
2. API 기본값과 브라우저 호출값을 동시에 검토한다.
3. 히스토리 패널 성능에 미치는 영향까지 확인한다.

## 8. 관련 문서

- `docs/api/overview.md`
- `docs/api/chat.md`
- `docs/static/ui.md`
