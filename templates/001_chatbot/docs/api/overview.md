# API 모듈 레퍼런스

이 문서는 `src/chatbot/api` 계층의 구조, 책임, 변경 지점을 코드 기준으로 정리한다.

## 1. 역할

`src/chatbot/api`는 HTTP 경계다. 이 계층의 책임은 다음으로 한정된다.

1. FastAPI 앱 생성과 라우터 등록
2. 요청/응답 DTO 검증
3. 도메인 예외를 HTTP 응답으로 변환
4. 런타임 조립 인스턴스를 `Depends`로 주입
5. 정적 UI를 `/ui`로 마운트

이 계층이 직접 하지 않는 일:

1. 채팅 그래프 분기 규칙 결정
2. 메시지 저장소 구현
3. 큐/버퍼 내부 동작 구현
4. LLM 호출 세부 구현

## 2. 디렉터리 구조

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

| 경로 | 코드 설명 | 유지보수 포인트 |
| --- | --- | --- |
| `src/chatbot/api/main.py` | 앱 생성, `/ui` 마운트, 라우터 등록, 종료 훅 관리 | 환경 변수 로딩은 라우터 import보다 먼저 유지해야 한다 |
| `src/chatbot/api/const` | Chat/UI API 경로 상수 정의 | 하드코딩 경로를 추가하지 말고 상수 파일에 먼저 반영한다 |
| `src/chatbot/api/chat` | 작업 제출, SSE 구독, 세션 스냅샷 API | `request_id` 기반 계약을 깨지 않도록 주의한다 |
| `src/chatbot/api/ui` | 세션 생성/목록/삭제와 메시지 목록 조회 API | UI DTO와 정적 UI 소비 필드를 함께 맞춘다 |
| `src/chatbot/api/health` | 프로세스 생존 확인 API | `/health`는 저비용 고정 응답으로 유지한다 |

## 3. 앱 초기화 흐름

`src/chatbot/api/main.py` 기준 실행 순서:

1. `RuntimeEnvironmentLoader().load()`가 루트 `.env`와 환경별 `.env`를 로드한다.
2. 환경 변수를 읽는 노드/서비스가 올바른 값을 사용하도록, 그 다음에 라우터와 런타임 모듈을 import한다.
3. `FastAPI(lifespan=...)`를 생성한다.
4. `/ui`에 `src/chatbot/static`을 마운트한다.
5. `health -> chat -> ui` 순서로 라우터를 등록한다.
6. 종료 시 `shutdown_chat_api_service()`가 실행되어 워커와 저장소 리소스를 정리한다.

## 4. 공개 HTTP 인터페이스

| 영역 | Method | Path | 상태코드 | 응답 모델 |
| --- | --- | --- | --- | --- |
| Health | `GET` | `/health` | `200` | 고정 JSON |
| Chat | `POST` | `/chat` | `202` | `SubmitChatResponse` |
| Chat | `GET` | `/chat/{session_id}/events` | `200` | SSE |
| Chat | `GET` | `/chat/{session_id}` | `200` | `SessionSnapshotResponse` |
| UI | `POST` | `/ui-api/chat/sessions` | `201` | `UICreateSessionResponse` |
| UI | `GET` | `/ui-api/chat/sessions` | `200` | `UISessionListResponse` |
| UI | `GET` | `/ui-api/chat/sessions/{session_id}/messages` | `200` | `UIMessageListResponse` |
| UI | `DELETE` | `/ui-api/chat/sessions/{session_id}` | `200` | `UIDeleteSessionResponse` |

## 5. 예외 처리 규칙

예외는 모두 `BaseAppException`에서 시작해 라우터 공통 함수에서 HTTP 예외로 바뀐다.

| 파일 | 역할 |
| --- | --- |
| `src/chatbot/api/chat/routers/common.py` | Chat API용 상태코드 매핑 |
| `src/chatbot/api/ui/routers/common.py` | UI API용 상태코드 매핑 |

현재 주요 매핑:

1. `CHAT_SESSION_NOT_FOUND` -> `404`
2. `CHAT_MESSAGE_EMPTY`, `CHAT_STREAM_NODE_INVALID` -> `400`
3. `CHAT_JOB_QUEUE_FAILED` -> `503`
4. `CHAT_STREAM_TIMEOUT` -> `504`
5. 그 외 -> `500`

## 6. 유지보수 포인트

1. DTO 필드명은 정적 UI와 문서가 직접 소비하므로, 이름을 바꾸면 `docs/static/ui.md`와 함께 갱신해야 한다.
2. `SessionSnapshotResponse.messages`는 현재 `limit=200` 고정 조회이므로, 값 변경 시 UI 동기화 전략도 함께 검토해야 한다.
3. API 라우터는 구현체를 직접 생성하지 않고 `runtime.py`나 서비스 팩토리에서만 주입받아야 한다.
4. `/health`는 readiness가 아니라 liveness 성격이므로 외부 의존성 점검을 섞지 않는 편이 안전하다.

## 7. 추가 개발과 확장 가이드

### 7-1. 새 Chat 엔드포인트 추가

1. `src/chatbot/api/chat/models`에 DTO를 추가한다.
2. `src/chatbot/api/chat/routers`에 라우터를 추가한다.
3. `src/chatbot/api/chat/routers/router.py`에 등록한다.
4. 실행 로직은 `shared` 서비스 계층에 위임한다.

### 7-2. UI 조회 응답 확장

1. `src/chatbot/api/ui/models`와 `src/chatbot/api/ui/utils/mappers.py`를 먼저 맞춘다.
2. 필요한 데이터가 없으면 `shared` 저장소/서비스 계층을 확장한다.
3. 프런트엔드가 사용하는 필드는 `docs/static/ui.md`까지 함께 갱신한다.

### 7-3. 런타임 교체

1. 큐, 이벤트 버퍼, 저장소 변경은 `src/chatbot/api/chat/services/runtime.py`에서만 조립한다.
2. 라우터에 분기 로직을 추가하지 않는다.
3. 앱 종료 훅과 리소스 정리 계약을 유지한다.

## 8. 관련 문서

- `docs/api/chat.md`
- `docs/api/ui.md`
- `docs/api/health.md`
- `docs/core/chat.md`
- `docs/static/ui.md`
