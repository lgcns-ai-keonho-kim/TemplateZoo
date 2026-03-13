# API 모듈

## 엔드포인트

| 영역 | Method | Path | 설명 |
| --- | --- | --- | --- |
| Health | `GET` | `/health` | 프로세스 생존 확인 |
| Chat | `POST` | `/chat` | 채팅 작업 제출 |
| Chat | `GET` | `/chat/{session_id}/events` | 요청 단위 SSE 구독 |
| Chat | `GET` | `/chat/{session_id}` | 세션 스냅샷 조회 |
| UI | `POST` | `/ui-api/chat/sessions` | 세션 생성 |
| UI | `GET` | `/ui-api/chat/sessions` | 세션 목록 |
| UI | `GET` | `/ui-api/chat/sessions/{session_id}/messages` | 메시지 목록 |
| UI | `DELETE` | `/ui-api/chat/sessions/{session_id}` | 세션과 메시지 삭제 |

## 런타임 조립

- `api/main.py`는 환경 로드, 라우터 등록, `/ui` 정적 파일 마운트, 종료 시 `shutdown_chat_api_service()` 호출을 담당한다.
- Chat 런타임 조립은 `src/rag_chatbot/api/chat/services/runtime.py` 한 곳에 고정된다.
- 기본 조립은 `ChatHistoryRepository + ChatService + ServiceExecutor + InMemoryQueue + InMemoryEventBuffer`다.
- API 계층은 조립된 싱글턴을 `Depends`로 주입받고, 라우터에서 직접 저장소나 엔진을 생성하지 않는다.

## 경계

- `api/chat`은 작업 제출, SSE 구독, 세션 스냅샷만 처리한다.
- `api/ui`는 UI 전용 세션/메시지 CRUD만 처리한다.
- `api/health`는 liveness만 처리한다.
