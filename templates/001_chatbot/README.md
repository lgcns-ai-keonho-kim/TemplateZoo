# 001 Chatbot Template

Python/FastAPI 기반의 채팅 애플리케이션 템플릿이다.
현재 기본 런타임은 `Gemini + SQLite + InMemoryQueue + InMemoryEventBuffer + 정적 UI` 조합으로 동작한다.

## 1. 빠른 시작

### 1-1. 프로젝트명 초기화(선택)

```bash
bash init.sh my-project
```

- `PROJECT_SLUG`: `my-project`
- `PACKAGE_NAME`: `my_project`

### 1-2. 의존성 설치

```bash
uv venv .venv
uv sync
```

### 1-3. 환경 변수 준비

루트 설정 파일:

```bash
cp .env.sample .env
```

기본 로컬 실행에 필요한 최소 예시:

```env
ENV=local
LOG_STDOUT=1
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_PROJECT=your-project
GEMINI_API_KEY=
CHAT_DB_PATH=data/db/chat/chat_history.sqlite
```

`ENV=dev`, `stg`, `prod`를 사용할 때는 루트 `.env` 외에 환경별 실제 `.env` 파일도 필요하다.

```bash
cp src/chatbot/resources/dev/.env.sample src/chatbot/resources/dev/.env
```

`RuntimeEnvironmentLoader`는 아래 순서로 값을 읽는다.

1. 프로젝트 루트 `.env`
2. `ENV` 또는 `APP_ENV` 또는 `APP_STAGE`
3. 필요 시 `src/chatbot/resources/<env>/.env`

### 1-4. 서버 실행

```bash
uv run uvicorn chatbot.api.main:app --host 0.0.0.0 --port 8000 --reload
```

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 정적 UI: `http://127.0.0.1:8000/ui`

## 2. 현재 동작 방식

현재 시스템은 `세션 + 비동기 실행 + SSE` 구조다.

1. 브라우저 UI는 `/ui-api/chat/sessions`와 `/ui-api/chat/sessions/{session_id}/messages`로 이력을 조회한다.
2. 사용자가 메시지를 보내면 `POST /chat`이 작업을 큐에 적재한다.
3. 서버는 즉시 `session_id`, `request_id`, `status=QUEUED`를 반환한다.
4. 브라우저는 약 1초 뒤 `GET /chat/{session_id}/events?request_id=...`로 SSE를 구독한다.
5. `ServiceExecutor`가 큐를 소비하면서 `start -> token* -> done/error` 이벤트를 공개 페이로드로 변환한다.
6. `ChatService`는 사용자 메시지 저장, 최근 문맥 구성, 그래프 실행, assistant 응답 저장을 담당한다.
7. 완료 응답은 `request_id` 기준으로 1회만 저장된다.

SSE `data` 예시:

```json
{
  "session_id": "session-1",
  "request_id": "request-1",
  "type": "token",
  "node": "response",
  "content": "안녕하세요",
  "status": null,
  "error_message": null,
  "metadata": null
}
```

## 3. 공개 API 요약

### 3-1. Chat API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/chat` | 채팅 작업 제출 |
| `GET` | `/chat/{session_id}` | 세션 스냅샷 조회 |
| `GET` | `/chat/{session_id}/events?request_id=...` | 요청 단위 SSE 구독 |

### 3-2. UI API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/ui-api/chat/sessions` | UI 세션 생성 |
| `GET` | `/ui-api/chat/sessions` | UI 세션 목록 조회 |
| `GET` | `/ui-api/chat/sessions/{session_id}/messages` | UI 메시지 목록 조회 |
| `DELETE` | `/ui-api/chat/sessions/{session_id}` | 세션 삭제 |

### 3-3. Health API

| Method | Path | 설명 |
| --- | --- | --- |
| `GET` | `/health` | 서버 liveness 확인 |

## 4. 기본 런타임 설정

실제로 기본 경로에서 쓰는 핵심 값은 아래와 같다.

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ENV` | 비어 있으면 `local` | 런타임 환경 선택 |
| `LOG_STDOUT` | `0` | stdout JSON 로그 출력 여부 |
| `GEMINI_MODEL` | 빈 문자열 | 응답/세이프가드 노드 모델명 |
| `GEMINI_PROJECT` | 빈 문자열 | Gemini 프로젝트 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | SQLite 저장 경로 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | 세션 메모리 최대 메시지 수 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | 스트림 실행 제한 시간 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | 완료 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | 완료 저장 재시도 간격 |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | 작업 큐 최대 크기 |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | 작업 큐 poll timeout |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | 이벤트 버퍼 최대 크기 |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | 이벤트 버퍼 poll timeout |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | 이벤트 버퍼 TTL |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | 인메모리 버퍼 GC 주기 |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | Redis 이벤트 버퍼 key prefix |

주의:

- `.env.sample`에는 `OPENAI_*`, `CHAT_TASK_*`, `CHAT_BUFFER_BACKEND` 같은 보관용 키가 남아 있지만, 현재 기본 런타임은 직접 사용하지 않는다.
- 설정을 바꾼 뒤에는 프로세스를 재시작해야 한다. 일부 노드와 서비스는 import 시점에 환경 값을 읽는다.

## 5. 프로젝트 구조

```text
src/chatbot/
  api/                # FastAPI 진입점과 HTTP DTO/라우터
  core/               # 채팅 도메인 모델, 프롬프트, 노드, 그래프
  shared/             # 실행 서비스, 저장소, 메모리, 런타임 유틸
  integrations/       # DB/LLM/FS 연동 어댑터
  resources/          # dev/stg/prod 환경별 리소스 파일
  static/             # 정적 UI 리소스
tests/                # pytest 테스트
docs/                 # 코드 기준 문서
data/                 # 기본 로컬 실행 데이터
```

## 6. 문서 진입점

- 개발 문서 허브: `docs/README.md`
- API 구조: `docs/api/overview.md`
- 채팅 그래프와 상태: `docs/core/chat.md`
- 실행 서비스와 저장소: `docs/shared/chat/overview.md`
- 외부 연동: `docs/integrations/overview.md`
- 환경 변수와 로컬 실행: `docs/setup/overview.md`
- 정적 UI 흐름: `docs/static/ui.md`
