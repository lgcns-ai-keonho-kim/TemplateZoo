# API 모듈 가이드

이 문서는 `src/rag_chatbot/api` 계층이 현재 어떤 HTTP 경계를 제공하는지와, 어디까지를 API 책임으로 볼지 정리한다.

## 1. 책임 경계

- `api/main.py`는 환경 로드, 라우터 등록, `/ui` 정적 파일 마운트, `/ -> /docs` 리다이렉트, 종료 시 `shutdown_chat_api_service()` 호출을 담당한다.
- `api/chat`은 작업 제출, SSE 구독, 세션 스냅샷만 처리하고 실제 실행은 `shared/chat/services`로 위임한다.
- `api/ui`는 UI 전용 세션/메시지 CRUD를 제공하며 자체 저장소를 만들지 않는다.
- `api/health`는 liveness만 확인한다. readiness나 외부 의존성 점검은 포함하지 않는다.

## 2. 현재 엔드포인트

| 영역 | Method | Path | 설명 |
| --- | --- | --- | --- |
| Health | `GET` | `/health` | 프로세스 생존 확인 |
| Chat | `POST` | `/chat` | 채팅 작업 제출 |
| Chat | `GET` | `/chat/{session_id}/events` | 요청 단위 SSE 구독 |
| Chat | `GET` | `/chat/{session_id}` | 세션 스냅샷 조회 |
| UI | `POST` | `/ui-api/chat/sessions` | 세션 생성 |
| UI | `GET` | `/ui-api/chat/sessions` | 세션 목록 |
| UI | `GET` | `/ui-api/chat/sessions/{session_id}/messages` | 메시지 목록 |
| UI | `DELETE` | `/ui-api/chat/sessions/{session_id}` | 세션 삭제 |

## 3. 런타임 조립 포인트

- 실제 Chat 런타임 조립은 `src/rag_chatbot/api/chat/services/runtime.py` 한 곳에 고정된다.
- 현재 조립값은 `ChatHistoryRepository + ChatService + ServiceExecutor + InMemoryQueue + InMemoryEventBuffer`다.
- API 계층은 이 싱글턴을 `Depends`로 받기만 하고 직접 생성하지 않는다.

## 4. 유지보수/추가개발 포인트

- 새 API를 추가할 때는 라우터 파일만 늘리지 말고, DTO와 예외 매핑, 상위 overview 문서까지 같이 수정한다.
- SSE payload를 바꾸면 `docs/api/chat.md`와 `docs/static/ui.md`를 반드시 함께 갱신해야 한다.
- 라우터에서 직접 엔진이나 저장소를 생성하지 않고 `runtime.py` 조립 경계를 유지하는 편이 변경 영향도를 줄인다.

## 5. 관련 문서

- `docs/api/chat.md`
- `docs/api/ui.md`
- `docs/api/health.md`
- `docs/shared/chat/README.md`
- `docs/shared/runtime.md`
