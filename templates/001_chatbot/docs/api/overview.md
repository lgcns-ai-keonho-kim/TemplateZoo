# API 모듈 레퍼런스

`src/chatbot/api`는 HTTP 경계다. 이 계층은 요청 검증, 응답 직렬화, 예외 변환, 정적 UI 마운트, 런타임 의존성 주입만 담당한다.

## 1. 책임

이 계층이 하는 일:

1. `FastAPI` 앱 생성
2. `/health`, `/chat`, `/ui-api/chat` 라우터 등록
3. 요청/응답 DTO 검증
4. `BaseAppException`을 HTTP 예외로 변환
5. `ChatService`, `ServiceExecutor` 같은 런타임 인스턴스를 `Depends`로 주입
6. 정적 UI를 `/ui`에 마운트

이 계층이 하지 않는 일:

1. 그래프 분기 규칙 결정
2. 저장소 구현
3. 큐/이벤트 버퍼 내부 동작 구현
4. LLM 호출 세부 처리

## 2. 구조

```text
src/chatbot/api/
  main.py
  const/
  chat/
    models/
    routers/
    services/
    utils/
  ui/
    models/
    routers/
    services/
    utils/
  health/
    routers/
```

## 3. 초기화 흐름

`src/chatbot/api/main.py` 기준:

1. `RuntimeEnvironmentLoader().load()`가 루트 `.env`와 환경별 `.env`를 먼저 로드한다.
2. 그 다음 Chat/UI/Health 라우터와 런타임 모듈을 import한다.
3. `FastAPI(lifespan=...)`를 생성한다.
4. `/ui`에 `src/chatbot/static`을 마운트한다.
5. `health -> chat -> ui` 순서로 라우터를 등록한다.
6. 앱 종료 시 `shutdown_chat_api_service()`가 실행된다.
7. `/`는 `/docs`로 리다이렉트된다.

## 4. 공개 인터페이스

| 영역 | Method | Path | 상태코드 | 응답 |
| --- | --- | --- | --- | --- |
| Health | `GET` | `/health` | `200` | `{"status": "ok"}` |
| Chat | `POST` | `/chat` | `202` | `SubmitChatResponse` |
| Chat | `GET` | `/chat/{session_id}/events` | `200` | SSE |
| Chat | `GET` | `/chat/{session_id}` | `200` | `SessionSnapshotResponse` |
| UI | `POST` | `/ui-api/chat/sessions` | `201` | `UICreateSessionResponse` |
| UI | `GET` | `/ui-api/chat/sessions` | `200` | `UISessionListResponse` |
| UI | `GET` | `/ui-api/chat/sessions/{session_id}/messages` | `200` | `UIMessageListResponse` |
| UI | `DELETE` | `/ui-api/chat/sessions/{session_id}` | `200` | `UIDeleteSessionResponse` |

## 5. 예외 처리

라우터 공통 변환기:

- Chat API: `src/chatbot/api/chat/routers/common.py`
- UI API: `src/chatbot/api/ui/routers/common.py`

현재 주요 매핑:

1. `CHAT_SESSION_NOT_FOUND` -> `404`
2. `CHAT_MESSAGE_EMPTY`, `CHAT_STREAM_NODE_INVALID` -> `400`
3. `CHAT_JOB_QUEUE_FAILED` -> `503`
4. `CHAT_STREAM_TIMEOUT` -> `504`
5. 그 외 -> `500`

## 6. 유지보수 포인트

1. DTO 필드명은 정적 UI가 그대로 소비하므로, 이름을 바꾸면 `docs/static/ui.md`도 함께 수정해야 한다.
2. `SessionSnapshotResponse.messages`는 현재 `limit=200` 고정 조회다.
3. 런타임 생성 로직은 라우터가 아니라 `src/chatbot/api/chat/services/runtime.py`에만 둔다.
4. `/health`는 readiness가 아니라 liveness 용도다.

## 7. 관련 문서

- `docs/api/chat.md`
- `docs/api/ui.md`
- `docs/api/health.md`
- `docs/core/chat.md`
- `docs/static/ui.md`
