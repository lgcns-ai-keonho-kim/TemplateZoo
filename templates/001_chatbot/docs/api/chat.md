# API Chat 레퍼런스

이 문서는 `src/chatbot/api/chat`의 엔드포인트, DTO, SSE 계약을 코드 기준으로 설명한다.

## 1. 디렉터리 구조

```text
src/chatbot/api/chat/
  models/
    message.py
    session.py
    stream.py
  routers/
    create_chat.py
    stream_chat_events.py
    get_chat_session.py
    common.py
    router.py
  services/
    runtime.py
  utils/
    mappers.py
```

| 경로 | 코드 설명 | 유지보수 포인트 |
| --- | --- | --- |
| `models/stream.py` | 작업 제출 요청/응답, 세션 스냅샷, SSE payload 모델 | 필드명 변경 시 프런트엔드와 SSE 소비 로직을 함께 수정한다 |
| `routers/create_chat.py` | `POST /chat` 구현 | 상태코드는 `202`를 유지한다 |
| `routers/stream_chat_events.py` | `GET /chat/{session_id}/events` 구현 | `request_id` 검증 계약을 유지한다 |
| `routers/get_chat_session.py` | 세션 상태/메시지 스냅샷 조회 | 메시지 조회 한도 `200` 고정값을 바꿀 때 영향 범위를 확인한다 |
| `services/runtime.py` | `ChatService`, `ServiceExecutor`, 큐/버퍼 조립 | 현재 기본 런타임은 InMemory 구현이다 |
| `utils/mappers.py` | 도메인 메시지/세션을 API DTO로 변환 | 직렬화 형식 변경 시 매퍼부터 수정한다 |

## 2. DTO 계약

### 2-1. 작업 제출

`SubmitChatRequest`

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `session_id` | `str \| None` | 생략 가능 |
| `message` | `str` | 최소 길이 1 |
| `context_window` | `int` | `1 <= value <= 100`, 기본값 20 |

`SubmitChatResponse`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `str` | 신규 또는 기존 세션 ID |
| `request_id` | `str` | 작업 1건 식별자 |
| `status` | `"QUEUED"` | 큐 적재 상태 |

### 2-2. 세션 스냅샷

`SessionSnapshotResponse`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `str` | 조회 대상 세션 |
| `messages` | `list[MessageResponse]` | 최근 저장된 메시지 목록 |
| `last_status` | `str \| None` | 실행기의 최근 세션 상태, 없으면 `"IDLE"` |
| `updated_at` | `datetime \| None` | 세션 마지막 갱신 시각 |

### 2-3. SSE payload

`StreamPayload`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `str` | 세션 ID |
| `request_id` | `str` | 작업 ID |
| `type` | `start \| token \| done \| error` | 이벤트 타입 |
| `node` | `str` | 이벤트를 만든 노드 이름 |
| `content` | `str` | 토큰/최종 응답 본문 |
| `status` | `str \| None` | 완료 상태 |
| `error_message` | `str \| None` | 오류 메시지 |
| `metadata` | `dict[str, object] \| None` | 부가 메타데이터 |

## 3. 엔드포인트

### 3-1. `POST /chat`

- 상태코드: `202 Accepted`
- 구현: `src/chatbot/api/chat/routers/create_chat.py`

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

동작:

1. `ServiceExecutor.submit_job()`가 호출된다.
2. 작업 큐 적재 성공 시 즉시 `QUEUED`를 반환한다.
3. 메시지 본문 저장과 그래프 실행은 비동기 워커에서 처리된다.

### 3-2. `GET /chat/{session_id}/events`

- 상태코드: `200 OK`
- 구현: `src/chatbot/api/chat/routers/stream_chat_events.py`
- 필수 쿼리: `request_id`

SSE는 `text/event-stream`으로 반환되며, 각 블록의 `data:`는 `StreamPayload` 구조를 따른다.

핵심 규칙:

1. `done`와 `error`는 모두 종료 이벤트다.
2. 클라이언트는 `payload.request_id`가 현재 요청과 일치하는지 확인해야 한다.
3. `error`는 비정상 연결 종료가 아니라 오류 정보가 담긴 정상적인 종료 이벤트다.

### 3-3. `GET /chat/{session_id}`

- 상태코드: `200 OK`
- 구현: `src/chatbot/api/chat/routers/get_chat_session.py`

동작:

1. 세션이 없으면 `CHAT_SESSION_NOT_FOUND`로 `404`를 반환한다.
2. 메시지는 현재 `limit=200, offset=0`으로 조회한다.
3. `last_status`는 실행기 상태를 사용하고, 값이 없으면 `"IDLE"`을 응답한다.

## 4. SSE 이벤트 해석

| 타입 | 의미 | 주 사용 노드 |
| --- | --- | --- |
| `start` | 워커가 요청 처리를 시작함 | `executor` |
| `token` | 응답 토큰 또는 스트림 가능한 데이터 | 주로 `response` |
| `done` | 정상 완료 | `response`, `blocked`, `executor` |
| `error` | 오류 종료 | `executor` 또는 실행 중 노드 |

`blocked` 경로는 토큰 스트림이 아니라 `assistant_message` 기반 완료 응답으로 끝날 수 있다.

## 5. 런타임 조립 포인트

`src/chatbot/api/chat/services/runtime.py` 기준:

1. 기본 저장소는 `ChatHistoryRepository()`이며 SQLite를 사용한다.
2. 기본 작업 큐는 `InMemoryQueue`다.
3. 기본 이벤트 버퍼는 `InMemoryEventBuffer`다.
4. 스트림 타임아웃과 저장 재시도 정책은 환경 변수로 조정한다.
5. PostgreSQL/Redis 전환 예시는 주석으로 제공되지만, 기본 동작은 분기 없는 InMemory/SQLite 조합이다.

## 6. 유지보수 포인트

1. `request_id`는 작업 제출 응답, SSE 구독, 완료 저장 멱등성의 공통 키다.
2. `SessionSnapshotResponse.last_status`는 저장소가 아니라 실행기 메모리 상태를 읽기 때문에, 프로세스 재시작 후 초기화될 수 있다.
3. `context_window` 범위를 바꾸면 DTO 검증과 프런트엔드 기본값을 함께 맞춰야 한다.
4. 예외 코드가 추가되면 `routers/common.py` 상태코드 매핑 문서도 같이 갱신해야 한다.

## 7. 추가 개발과 확장 가이드

### 7-1. 새로운 이벤트 타입 추가

1. `StreamEventType` enum을 먼저 확장한다.
2. `ServiceExecutor`가 public payload를 만들도록 수정한다.
3. 정적 UI가 새 이벤트를 무시할지 소비할지 결정한다.
4. 기존 `start/token/done/error` 계약은 깨지 않도록 유지한다.

### 7-2. 세션 스냅샷 확장

1. 응답 모델에 필드를 추가한다.
2. `get_chat_session.py`에서 값을 채운다.
3. 프런트엔드가 실제로 사용할 필드만 노출한다.

### 7-3. 저장소/큐 교체

1. 조립은 `runtime.py`에서만 변경한다.
2. 라우터 시그니처와 응답 계약은 가능한 유지한다.
3. 기본값과 확장 경로를 문서에 분리해 적는다.

## 8. 관련 문서

- `docs/api/overview.md`
- `docs/core/chat.md`
- `docs/static/ui.md`
