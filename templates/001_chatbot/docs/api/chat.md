# API Chat 레퍼런스

이 문서는 `src/chatbot/api/chat` 모듈의 HTTP 인터페이스와 SSE 종료 동작을 코드 기준으로 설명한다.

## 1. 핵심 용어

| 용어 | 의미 |
| --- | --- |
| `session_id` | 대화 컨텍스트 식별자 |
| `request_id` | 작업 제출 1건 식별자 |
| SSE | `/chat/{session_id}/events` 이벤트 스트림 |
| 종료 이벤트 | `done` 또는 `error` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/chatbot/api/chat/routers/create_chat.py` | `POST /chat` |
| `src/chatbot/api/chat/routers/stream_chat_events.py` | `GET /chat/{session_id}/events` |
| `src/chatbot/api/chat/services/runtime.py` | 실행기/서비스 조립 |
| `src/chatbot/shared/chat/services/service_executor.py` | 이벤트 생성/정규화/종료 |

## 3. HTTP 인터페이스

### 3-1. 작업 제출

- Method: `POST`
- Path: `/chat`
- Status: `202 Accepted`

요청 예시:

```json
{
  "session_id": "3f3b...",
  "message": "요약해줘",
  "context_window": 20
}
```

응답 예시:

```json
{
  "session_id": "3f3b...",
  "request_id": "28c7...",
  "status": "QUEUED"
}
```

### 3-2. 이벤트 구독(SSE)

- Method: `GET`
- Path: `/chat/{session_id}/events`
- Query: `request_id` 필수
- Status: `200 OK`
- Content-Type: `text/event-stream`

핵심 동작:

1. 스트림 종료 이벤트는 `done` 또는 `error`다.
2. `error` 종료는 비정상 연결이 아니라, 원인 정보가 포함된 정상 종료 시그널이다.
3. 테스트/클라이언트는 `done`만 강제하지 말고 `done|error`를 모두 처리해야 한다.

## 4. 이벤트 인터페이스

| type | 설명 | 종료 여부 |
| --- | --- | --- |
| `start` | 실행 시작 | 아니오 |
| `token` | 토큰 단위 본문 | 아니오 |
| `done` | 정상 완료 | 예 |
| `error` | 오류 종료 | 예 |

`error` payload 확인 포인트:

1. `status=FAILED`
2. `error_message`
3. `metadata.error_code`

## 5. 타임아웃 정렬 레퍼런스

타임아웃은 서버/클라이언트를 함께 맞춰야 한다.

1. 서버: `CHAT_STREAM_TIMEOUT_SECONDS`
2. 클라이언트(E2E): HTTP read timeout

권장:

1. 클라이언트 read timeout >= 서버 timeout + 여유 시간
2. 느린 LLM 환경에서는 두 값을 함께 상향

## 6. 트러블슈팅

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| 작업 제출 성공 후 이벤트 없음 | 워커 미동작/서버 초기화 실패 | `/health`, 서버 로그, runtime 조립 확인 |
| `done` 미수신 | 실제 `error` 종료 | `error_message`와 `error_code` 확인 |
| SSE `ReadTimeout` | 클라이언트 timeout 과소 | 서버/클라이언트 timeout 동시 상향 |
| E2E `Connection refused` | 서버 기동 지연/초기화 실패 | 기동 대기 시간 상향 + stdout/stderr 점검 |

## 7. 관련 문서

- `docs/shared/chat.md`
- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
