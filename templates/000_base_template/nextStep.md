# Next Step: Chat API 분리안 정리

## 목적

- 요청 접수와 스트리밍 수신 책임을 분리해 구조를 단순화한다.
- Redis를 중간 버퍼로 사용하되, 최종 중계는 백엔드 SSE 계층이 담당하도록 유지한다.
- 재시도, 재연결, 멀티 인스턴스 확장 시 동작을 예측 가능하게 만든다.
- 작업 분배(JobQueue)와 스트림 전달(EventBuffer) 책임을 분리한다.

## 예시 API

- `POST /chat`
  - 역할: 사용자 메시지 제출(작업 생성)
  - 응답: `202 Accepted`
  - 본문 예시:
    - `session_id` (없으면 서버 생성)
    - `message`
    - `context_window`
  - 응답 예시:
    - `session_id`
    - `request_id`
    - `status` (`QUEUED`)

- `GET /chat/{session_id}`
  - 역할: 세션 상태/메시지 스냅샷 조회
  - 비스트리밍 조회 전용
  - 응답 예시:
    - `session_id`
    - `messages`
    - `last_status`
    - `updated_at`

- `GET /chat/{session_id}/events`
  - 역할: SSE 스트림 구독
  - 이벤트 타입:
    - `start`
    - `token`
    - `done`
    - `error`

## 처리 흐름

1. 클라이언트가 `POST /chat`으로 메시지를 제출한다.
2. 백엔드가 작업 큐(JobQueue)에 작업을 저장하고 `request_id`를 반환한다.
3. 워커(또는 실행기)가 JobQueue를 소비하며 그래프를 실행한다.
4. 실행 중 생성된 이벤트는 이벤트 버퍼(EventBuffer)에 기록된다.
5. SSE 핸들러는 EventBuffer에서 이벤트를 즉시 `pop`하여 `data: {...}`로 중계한다.
6. 실행기는 토큰을 내부 버퍼에 누적하고, 생성 완료 시 `done` 이벤트를 먼저 발행한다.
7. `done` 발행 이후 대화 내역 저장은 비동기 후처리로 수행한다.
8. 저장 실패는 `error` 대신 서버 보상 로직(재시도 큐/로그/모니터링)으로 처리한다.

## 런타임 구조 분리안

- `shared/runtime/queue`:
  - 역할: 작업 큐(JobQueue)
  - 대상: `POST /chat`로 들어온 실행 요청
  - 소비자: 워커(그래프 실행기)
  - 비고: 기존 `InMemoryQueue`, `RedisQueue`는 JobQueue 용도로 유지한다.

- `shared/runtime/buffer` (신규):
  - 역할: 스트림 이벤트 버퍼(EventBuffer)
  - 대상: `start/token/done/error` 이벤트
  - 소비자: SSE 핸들러(`GET /chat/{session_id}/events`)
  - 비고: 즉시 소비(pop) 기반으로 동작하며, 프론트는 SSE만 구독한다.

## 패키지/인터페이스 제안

- `src/base_template/shared/runtime/queue`:
  - 책임: 작업 생성/분배(Producer: API, Consumer: 워커)
  - API 예시:
    - `enqueue(job: JobPayload) -> QueueItem`
    - `dequeue(timeout: float | None) -> QueueItem | None`

- `src/base_template/shared/runtime/buffer` (신규):
  - 책임: 실행 중 이벤트 전달(Producer: 워커, Consumer: SSE)
  - 내부 이벤트 모델(`StreamEvent`) 기준:
    - `event`: `start | token | done | error`
    - `data`: `str | dict | null`
    - `node`: `str | null`
    - `request_id`: `str`
    - `metadata`: `dict | null` (선택, 생략 가능)
  - API 예시:
    - `push(session_id: str, request_id: str, event: StreamEvent) -> None`
    - `pop(session_id: str, request_id: str, timeout: float | None) -> StreamEvent | None`
    - `cleanup(session_id: str, request_id: str) -> None`

- 구현체 전환:
  - 로컬/테스트: `InMemoryJobQueue + InMemoryEventBuffer`
  - 운영: `RedisJobQueue + RedisEventBuffer`
  - 선택 방식: 환경 변수(`QUEUE_BACKEND`, `BUFFER_BACKEND`) 기반 팩토리

## Redis 사용 원칙

- Redis는 **즉시 소비형 버퍼 큐** 역할만 수행한다.
- 브라우저는 Redis를 직접 읽지 않는다.
- SSE가 이벤트를 꺼내면 큐 데이터는 즉시 제거된다.
- 키 전략:
  - 권장: 요청 단위 분리 `chat:stream:{session_id}:{request_id}`
  - 최소: 세션 단위 분리 `chat:stream:{session_id}`
- 정리 전략:
  - `done/error` 후 빈 큐 정리 또는 TTL 적용
  - 오래된 키 주기적 정리

## 이벤트 페이로드 기준안

- 내부 이벤트(EventBuffer 저장 스키마):
  - `event` (`start|token|done|error`)
  - `data`
  - `node`
  - `request_id`
  - `metadata` (선택)

- 외부 이벤트(SSE 응답 스키마):
  - `session_id`
  - `request_id`
  - `type` (`start|token|done|error`)
  - `node`
  - `content`
  - `status`
  - `error_message`
  - `metadata` (선택)

- 내부 -> 외부 변환 규칙:
  - `event` -> `type`
  - `data` -> `content`
  - `node` -> `node`
  - `metadata`는 존재할 때만 `SSE data`에 포함하고, 없으면 필드를 생략한다.
  - 기본 전송 포맷 예시: `data: {"node":"response","type":"token",...}`

## RedisQueue 리팩토링/개선 포인트

- 공용 큐 키 제거:
  - 현재 단일 키 사용 시 세션 간 이벤트 혼선 가능성이 있다.
  - EventBuffer는 `session_id/request_id` 기준으로 키를 분리한다.

- 모듈 경계 재정의:
  - JobQueue 관련 코드는 `shared/runtime/queue`에 유지한다.
  - EventBuffer 관련 코드는 `shared/runtime/buffer`로 이동/신규 추가한다.

- 백엔드 전환 전략:
  - 로컬 테스트: `InMemoryJobQueue + InMemoryEventBuffer`
  - 운영 이관: `RedisJobQueue + RedisEventBuffer`
  - 전환은 환경 변수 기반 선택으로 처리한다.

- 역할 고정:
  - `RedisQueue`는 JobQueue 책임만 가진다.
  - 스트림 토큰 중계는 `RedisEventBuffer`로 완전히 분리한다.
  - 결과적으로 Queue는 "작업", Buffer는 "이벤트"만 다룬다.

- 이벤트 모델 명확화:
  - 큐에 저장되는 내부 이벤트와 SSE 외부 이벤트 스키마를 분리한다.
  - 내부 이벤트는 최소 필드(`event`, `data`, `node`, `request_id`, `metadata`)만 유지한다.
    - `metadata`는 token usage에 대한 정보나 RAG 응답에서 사용된 참고 문서들이 이에 해당한다.
    - `metadata`는 서비스의 구현 상황과 목적에 따라 갈리므로, 유연하게 주입받을 수 있는 구조여야한다. (생략 가능)

- 실행기 누적 저장 책임 고정:
  - SSE `GET` 엔드포인트는 중계만 담당한다.
  - 토큰 누적과 `done` 발행은 실행기(워커)에서 처리한다.
  - 저장은 `done` 발행 이후 비동기 후처리로 분리한다.

- 멱등성(idempotency) 처리:
  - `request_id` 단위로 저장 중복 방지 키를 둔다.
  - 재시도/재연결/저장 재처리 상황에서도 대화 저장은 1회만 수행한다.

- 실패 처리 기준:
  - `error` 이벤트는 생성 실패(모델/그래프 실행 실패) 전용으로 사용한다.
  - 저장 실패는 `done` 이후 비동기 경로에서 처리하며, 기본 SSE 계약에는 포함하지 않는다.
  - 저장 실패 원인은 서버 로그/모니터링에 표준 포맷으로 기록한다.
  - 필요 시 별도 운영 이벤트(`persist_error`)를 내부 채널로 발행할 수 있다.
  - `metadata`에는 민감정보(원문 전문, 비공개 키, 개인정보)를 포함하지 않는다.

## GET SSE 엔드포인트 원칙

- `GET /chat/{session_id}/events`는 큐 소비 + SSE 송신만 수행한다.
- 프론트 화면 표시를 위해 저장 완료를 기다리지 않는다.
- `done`은 생성 완료 신호이며 저장 완료 신호가 아니다.
- 조회 API는 `done` 직후 미반영 상태가 있을 수 있으므로 eventual consistency를 허용한다.
- `metadata`는 존재 시 그대로 전달하고, 없으면 필드를 생략한다.
- `metadata` 스키마는 고정하지 않고 서비스 목적에 맞게 확장 가능하도록 유지한다.

## 기대 효과

- 요청 처리와 응답 전송이 분리되어 장애 지점이 명확해진다.
- SSE 재연결 시 동일 세션 기준 복구 전략을 세우기 쉬워진다.
- 멀티 인스턴스 환경에서 처리 경로를 표준화할 수 있다.

## 원샷 적용 순서

1. 내부/외부 이벤트 스키마와 매핑 규칙(`metadata`, `node` 포함)을 문서/코드 계약으로 고정
2. `shared/runtime/buffer`를 신설하고 InMemory/Redis EventBuffer 구현을 완료한다.
3. 백엔드를 신규 흐름(`POST /chat` + `GET /chat/{session_id}/events`)으로 전환하고, 기존 `/chat/sessions/{session_id}/messages/stream`를 제거한다.
4. 프론트(static)를 동일 릴리스에서 신규 SSE 스키마(`type`, `node`, `content`, `request_id`, `metadata`) 기준으로 전환한다.
5. 실행기에서 `done 먼저 발행` + `done 이후 비동기 저장` + 저장 멱등성/재시도 정책 적용을 완료하고 배포한다.

## 프론트엔드(static) 영향 및 작업 항목

- `src/base_template/static/js/chat/api_transport.js`
  - 전송 경로를 2단계로 분리한다.
  - 1단계: `POST /chat` 호출로 `session_id`, `request_id`를 수신한다.
  - 2단계: `GET /chat/{session_id}/events` SSE 구독을 시작한다.
  - SSE 페이로드에서 `type`, `node`, `content`, `request_id`, `metadata`를 처리한다.
  - SSE `data:` 라인 결합 시 불필요한 trim을 하지 않고 공백/개행을 보존한다.

- `src/base_template/static/js/chat/chat_cell.js`
  - 셀 상태에 `activeRequestId`를 추가해 현재 요청과 이벤트를 매칭한다.
  - `token/done/error` 이벤트는 `request_id`가 일치할 때만 반영한다.
  - `node`를 기반으로 렌더링 정책을 분기한다.
  - 기본 정책: `node=response`의 `token`은 본문 버블에 누적하고, 그 외 `node`는 상태/디버그 정보로만 사용한다.
  - `done` 수신 시 최종 렌더 후 입력 상태를 복구하고, `error` 수신 시 오류 UI를 표시한다.

- `src/base_template/static/js/chat/chat_presenter.js`
  - 상태 영역에 현재 처리 `node`를 표시할 수 있는 렌더 함수를 추가한다.
  - `metadata`가 존재할 때 보조 정보(예: usage, 참고문서 개수)를 선택적으로 표시한다.

- `src/base_template/static/css/main.css`
  - 상태 영역의 `node` 뱃지/텍스트 스타일을 추가한다.
  - `metadata` 보조 정보 블록 스타일을 추가한다.

- `src/base_template/static/js/utils/markdown.js`
  - 스트리밍 중 토큰 누적 텍스트를 그대로 렌더링해 공백/개행 왜곡을 방지한다.
  - 코드 펜스는 열린 시점부터 코드블록 렌더를 시작하고 닫힘 확인 시 코드블록 렌더를 종료한다.

- 원샷 전환 기준
  - 구 SSE 포맷(`node`/`metadata` 없음)은 지원하지 않는다.
  - 프론트와 백엔드는 동일 릴리스에서 함께 배포한다.
  - 필수 필드(`type`, `request_id`) 누락 시 프로토콜 오류로 처리하고 스트림을 종료한다.

## 작업 큐 관련 결정사항

- 작업 큐는 제거하지 않는다.
- 작업 큐는 `POST /chat` 요청을 워커로 전달하는 용도로만 사용한다.
- 스트리밍 텍스트 중계 경로에는 작업 큐를 재사용하지 않는다.
- 스트리밍은 EventBuffer 경로(`worker -> buffer -> SSE`)로만 처리한다.

## 백엔드 원샷 전환 기준

- 구버전 API/이벤트 포맷 호환 코드는 추가하지 않는다.
- 기존 엔드포인트 `/chat/sessions/{session_id}/messages/stream`는 유지하지 않고 제거한다.
- 서버는 신규 계약(`POST /chat`, `GET /chat/{session_id}/events`)만 처리한다.
- 내부 이벤트 -> SSE 변환 시 필수 필드(`type`, `request_id`, `node`) 누락은 프로토콜 오류로 처리한다.
- 구버전 fallback 매핑(`event`만 있고 `type` 미존재 등)은 지원하지 않는다.
- 스트리밍 이벤트는 `EventBuffer` 전용으로 처리하고, `RedisQueue`는 `JobQueue` 전용으로만 사용한다.
- `done`은 생성 완료 기준으로 즉시 발행하고, 저장은 비동기 후처리로 분리한다.
- 배포는 프론트/백엔드 동시 반영을 전제로 진행한다.

## 2026-02-12 반영 현황

- 완료
  - E2E를 eventual consistency 기준으로 전환했다.
    - `done` 수신 직후 즉시 이력 조회를 단정하지 않고 polling 검증으로 변경했다.
  - `done 먼저 송신 -> 저장 비동기 후처리` 흐름을 실행기에 반영했다.
    - 실행기는 `done` 이벤트를 EventBuffer에 push한 뒤 저장 작업을 별도 후처리 워커로 위임한다.
    - 저장 실패는 기본 SSE `error`로 노출하지 않고 재시도/로그 경로로 분리한다.
  - `request_id` 저장 멱등성 기록 경로를 추가했다.
    - `chat_request_commits` 컬렉션을 신설하고 `request_id` 기준 커밋 여부를 확인한다.
  - LLM provider 선택을 노드 공용 팩토리로 통합했다.
    - `CHAT_LLM_PROVIDER` 기준으로 `openai|gemini`를 명시적으로 분기한다.
  - Safeguard 토큰 표기를 `PROMPT_INJECTION`으로 통일했다.
    - 과거 오타(`PROMPT_INJETION`)는 alias로만 수용한다.
  - 공백/개행 보존 정책을 보강했다.
    - 백엔드 토큰/최종 본문 처리에서 불필요한 `strip()` 의존을 줄였다.
    - LLM content가 list(파트 배열)로 오는 경우 문자열 결합 규칙을 추가했다.
  - static markdown 렌더러의 fenced code 재분류 휴리스틱을 제거했다.
    - 코드펜스는 항상 코드블록으로 렌더링하고 하이라이트를 유지한다.
  - InMemoryEventBuffer 만료/정리 정책(TTL/GC)을 추가했다.
    - 설정: `in_memory_ttl_seconds`, `in_memory_gc_interval_seconds`
    - 런타임 환경변수: `CHAT_EVENT_BUFFER_TTL_SECONDS`, `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS`
  - `GET /chat/{session_id}`의 `last_status`를 런타임 상태 기반으로 확장했다.
    - `ServiceExecutor`가 `QUEUED|RUNNING|COMPLETED|FAILED`를 추적한다.
    - 상태 정보가 없는 초기 세션은 `IDLE`로 반환한다.

- 남은 항목
  - 현재 기준 핵심 전환 항목은 모두 반영 완료.
