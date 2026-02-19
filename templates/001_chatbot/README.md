# BASE TEMPLATE

LLM 기반 애플리케이션을 빠르게 시작하기 위한 Python/FastAPI 템플릿이다.  
권장 Python 버전은 `3.13+`이다.

## 1. 빠른 시작

### 1-1. 프로젝트명 초기화(선택)

```bash
bash init.sh my-project
```

- 단일 인자로 받는다.
- 내부에서 자동 변환:
- `PROJECT_SLUG`: `my-project` 형태
- `PACKAGE_NAME`: `my_project` 형태

### 1-2. 가상환경/의존성 설치

```bash
uv venv .venv
uv sync
```

### 1-3. 환경 변수 파일 생성

```bash
cp .env.sample .env
```

필수 값:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

## 2. 서버 실행

```bash
uv run uvicorn base_template.api.main:app --host 0.0.0.0 --port 8000 --reload
```

`.env`는 `RuntimeEnvironmentLoader`가 자동 로드한다.

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 정적 UI: `http://127.0.0.1:8000/ui`

## 3. API 인터페이스 요약

### 3-1. Chat API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/chat` | 채팅 작업 제출 (`session_id`, `message`, `context_window`) |
| `GET` | `/chat/{session_id}` | 세션 스냅샷(메시지/최근 상태) 조회 |
| `GET` | `/chat/{session_id}/events?request_id=...` | 요청 단위 SSE 이벤트 구독 |

### 3-2. UI API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/ui-api/chat/sessions` | UI 세션 생성 |
| `GET` | `/ui-api/chat/sessions` | UI 세션 목록 |
| `GET` | `/ui-api/chat/sessions/{session_id}/messages` | UI 메시지 목록 |
| `DELETE` | `/ui-api/chat/sessions/{session_id}` | 세션+메시지 삭제 |

## 4. 동작 방식

현재 시스템은 `세션 + 비동기 실행 + SSE` 구조로 동작한다.

1. UI는 `/ui-api/chat/sessions`로 세션 목록을 가져오고 활성 세션을 정한다.
2. 사용자가 메시지를 보내면 `POST /chat`을 호출한다.
3. 서버는 `session_id`, `request_id`, `status=QUEUED`를 즉시 반환한다.
4. UI는 `GET /chat/{session_id}/events?request_id=...`로 스트림을 구독한다.
5. `ServiceExecutor`가 큐를 소비하며 `start -> token* -> done/error` 이벤트를 보낸다.
6. 완료 시 assistant 응답은 `request_id` 멱등 기준으로 저장된다.
7. 필요하면 `GET /chat/{session_id}`로 최종 스냅샷을 조회한다.

SSE `data` 예시:

```json
{
  "session_id": "...",
  "request_id": "...",
  "type": "token",
  "node": "response",
  "content": "안녕하세요",
  "status": null,
  "error_message": null
}
```

이벤트 타입:

- `start`
- `token`
- `done`
- `error`

## 5. 환경 변수 (`.env`)

기본 샘플: `.env.sample`

전체 키 상세 설명과 반영 상태는 `docs/setup/env.md`를 참고한다.

### 5-1. 런타임/로그

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ENV` | (빈값) | `local/dev/stg/prod` 런타임 선택 |
| `LOG_STDOUT` | `1` | stdout JSON 로그 출력 여부 |

### 5-2. Chat 실행 핵심

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `OPENAI_API_KEY` | - | OpenAI API 키 |
| `OPENAI_MODEL` | - | OpenAI 모델명 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | Chat 이력 SQLite 경로 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | 세션 메모리 최대 메시지 수 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | SSE 대기/실행 타임아웃 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | 완료 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | 완료 저장 재시도 간격(초) |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | 작업 큐 최대 크기 (`0` 무제한) |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | 작업 큐 poll timeout(초) |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | 이벤트 버퍼 최대 크기 (`0` 무제한) |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | 이벤트 버퍼 pop timeout(초) |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | 이벤트 버퍼 TTL(초) |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | 인메모리 버퍼 GC 주기(초) |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | Redis 이벤트 키 prefix |

참고:

- `.env.sample`의 `CHAT_LLM_PROVIDER`, `GEMINI_*` 값은 확장/실험 설정이다.
- 현재 기본 노드(`core/chat/nodes/*.py`)는 `OPENAI_*` 환경 변수를 사용한다.

### 5-3. DB 연동(선택)

PostgreSQL, MongoDB, Redis, Elasticsearch, SQLite 관련 변수는 `.env.sample`을 참고한다.  
엔진별 사용 방법은 `docs/integrations/db.md`를 따른다.

## 6. 채팅 이력 초기화

기본 저장소는 SQLite(`CHAT_DB_PATH`)다.

전체 파일 초기화:

```bash
rm -f data/db/chat/chat_history.sqlite
```

테이블 데이터만 삭제:

```bash
sqlite3 data/db/chat/chat_history.sqlite "DELETE FROM chat_messages; DELETE FROM chat_sessions;"
```

## 7. 프로젝트 구조

```text
src/base_template/
  api/                  # FastAPI 라우터, DTO, DI 조립
  core/
    chat/               # 도메인 모델, 그래프, 노드, 프롬프트
  shared/
    chat/               # ChatService/ServiceExecutor/Repository/Memory
    runtime/            # Queue/EventBuffer/Worker/ThreadPool
    logging/            # 공통 로깅
    config/             # 설정/환경 로더
    exceptions/         # 공통 예외
    const/              # 공통 상수
  integrations/         # DB/LLM/FS 외부 연동 어댑터
  static/               # 정적 UI
tests/                  # pytest 테스트
docs/                   # 개발 문서
```

## 8. 문서 인덱스

| 문서 | 링크 | 설명 |
| --- | --- | --- |
| 문서 허브 | [docs/README.md](docs/README.md) | 전체 맵, 변경 진입점 |
| Setup 개요 | [docs/setup/overview.md](docs/setup/overview.md) | 인프라/환경 문서 인덱스 |
| Setup ENV | [docs/setup/env.md](docs/setup/env.md) | `.env` 키 전체 설명 |
| Setup SQLite Vec | [docs/setup/sqlite_vec.md](docs/setup/sqlite_vec.md) | SQLite + sqlite-vec 구성 |
| Setup PostgreSQL | [docs/setup/postgresql_pgvector.md](docs/setup/postgresql_pgvector.md) | PostgreSQL + pgvector 설치/연동 |
| Setup MongoDB | [docs/setup/mongodb.md](docs/setup/mongodb.md) | MongoDB 설치/연동 |
| Setup FileSystem | [docs/setup/filesystem.md](docs/setup/filesystem.md) | 파일 시스템 로그 연동 |
| API 개요 | [docs/api/overview.md](docs/api/overview.md) | API 계층 책임/라우팅 |
| API Chat | [docs/api/chat.md](docs/api/chat.md) | `/chat` 인터페이스, SSE |
| API UI | [docs/api/ui.md](docs/api/ui.md) | `/ui-api/chat` 인터페이스 |
| Core Chat | [docs/core/chat.md](docs/core/chat.md) | 그래프/노드 동작 |
| Shared Chat | [docs/shared/chat.md](docs/shared/chat.md) | 실행기/저장/멱등 |
| Shared Runtime | [docs/shared/runtime.md](docs/shared/runtime.md) | Queue/EventBuffer 구성 |
| Integrations DB | [docs/integrations/db.md](docs/integrations/db.md) | DB 엔진/셋업 |
| Integrations LLM | [docs/integrations/llm.md](docs/integrations/llm.md) | `LLMClient` 사용 |
| Integrations FS | [docs/integrations/fs.md](docs/integrations/fs.md) | 파일 저장소 경로/정책 |
| Static UI | [docs/static/ui.md](docs/static/ui.md) | UI 연동 순서/상태 관리 |

## 9. 테스트

전체:

```bash
uv run pytest
```

E2E 예시:

```bash
uv run pytest tests/e2e/test_chat_api_server_e2e.py -v -s
```
