# API Chat 레퍼런스

이 문서는 `src/chatbot/api/chat`의 공개 계약을 코드 기준으로 정리한다.

## 1. 구성 요소

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

핵심 책임:

1. `POST /chat`으로 작업 제출
2. `GET /chat/{session_id}/events`로 요청 단위 SSE 중계
3. `GET /chat/{session_id}`로 세션 스냅샷 조회

## 2. DTO 계약

### 2-1. `SubmitChatRequest`

| 필드 | 타입 | 제약 |
| --- | --- | --- |
| `session_id` | `str \| None` | 생략 가능 |
| `message` | `str` | 최소 길이 1 |
| `context_window` | `int` | `1 <= value <= 100`, 기본값 20 |

### 2-2. `SubmitChatResponse`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `str` | 신규 또는 기존 세션 ID |
| `request_id` | `str` | 요청 1건 식별자 |
| `status` | `"QUEUED"` | 큐 적재 상태 |

### 2-3. `SessionSnapshotResponse`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `str` | 조회 대상 세션 |
| `messages` | `list[MessageResponse]` | 현재 저장된 메시지 목록 |
| `last_status` | `str \| None` | 실행기의 최근 세션 상태 |
| `updated_at` | `datetime \| None` | 세션 마지막 갱신 시각 |

### 2-4. `StreamPayload`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `session_id` | `str` | 세션 ID |
| `request_id` | `str` | 요청 ID |
| `type` | `start \| token \| done \| error` | 이벤트 타입 |
| `node` | `str` | 이벤트를 만든 노드 이름 |
| `content` | `str` | 토큰 또는 완료 본문 |
| `status` | `str \| None` | 완료/실패 상태 |
| `error_message` | `str \| None` | 실패 메시지 |
| `metadata` | `dict[str, object] \| None` | 부가 메타데이터 |

## 3. 엔드포인트

### 3-1. `POST /chat`

- 상태코드: `202 Accepted`
- 구현: `src/chatbot/api/chat/routers/create_chat.py`

동작:

1. `ServiceExecutor.submit_job()`을 호출한다.
2. `session_id`가 없으면 새 세션을 먼저 만든다.
3. 성공 시 `QUEUED` 상태를 즉시 반환한다.

예시:

```json
{
  "session_id": "session-1",
  "message": "요약해줘",
  "context_window": 20
}
```

### 3-2. `GET /chat/{session_id}/events`

- 상태코드: `200 OK`
- 구현: `src/chatbot/api/chat/routers/stream_chat_events.py`
- 필수 쿼리: `request_id`

특징:

1. 반환 형식은 `text/event-stream`이다.
2. 각 `data:` 블록은 `StreamPayload` 형태다.
3. `done`와 `error`는 모두 종료 이벤트다.
4. 공개 페이로드는 `ServiceExecutor._build_public_payload()`가 만든다.

이벤트 의미:

| 타입 | 의미 | 대표 노드 |
| --- | --- | --- |
| `start` | 워커가 요청 처리 시작 | `executor` |
| `token` | 응답 토큰 또는 차단 메시지 조각 | 주로 `response`, 때때로 `blocked` |
| `done` | 정상 완료 | `response`, `blocked` |
| `error` | 오류 종료 | 주로 `executor` |

주의:

- `blocked` 경로의 `assistant_message`는 `ServiceExecutor`에서 공개 `token` 이벤트로 변환된다.
- 최종 `done` 이벤트의 `status`는 `COMPLETED`, `error` 이벤트의 `status`는 `FAILED`다.

### 3-3. `GET /chat/{session_id}`

- 상태코드: `200 OK`
- 구현: `src/chatbot/api/chat/routers/get_chat_session.py`

동작:

1. 세션이 없으면 `404`를 반환한다.
2. 메시지는 현재 `limit=200`, `offset=0`으로 조회한다.
3. `last_status`가 없으면 응답에 `"IDLE"`이 들어간다.

## 4. 런타임 조립

`src/chatbot/api/chat/services/runtime.py` 기준 기본값:

1. 저장소: `ChatHistoryRepository()` -> SQLite
2. 작업 큐: `InMemoryQueue`
3. 이벤트 버퍼: `InMemoryEventBuffer`
4. 그래프: `chat_graph`
5. 타임아웃: `CHAT_STREAM_TIMEOUT_SECONDS`
6. 저장 재시도: `CHAT_PERSIST_RETRY_LIMIT`, `CHAT_PERSIST_RETRY_DELAY_SECONDS`

주석에는 PostgreSQL, Redis 전환 예시가 있지만, 현재 기본 코드 경로는 분기 없는 InMemory/SQLite 조합이다.

## 5. 유지보수 포인트

1. `request_id`는 작업 제출 응답, SSE 구독, 완료 저장 멱등성의 공통 키다.
2. `context_window` 범위를 바꾸면 DTO와 정적 UI 기본값을 함께 검토해야 한다.
3. 공개 SSE 필드명(`type`, `node`, `content`, `status`, `error_message`, `metadata`)은 프런트 계약이다.
4. 새 예외 코드를 추가하면 `routers/common.py` 상태코드 매핑도 같이 갱신해야 한다.

## 6. 관련 문서

- `docs/api/overview.md`
- `docs/api/ui.md`
- `docs/core/chat.md`
- `docs/shared/chat/services/service_executor.md`
- `docs/static/ui.md`
