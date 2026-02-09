# BASE TEMPLATE

LLM 기반 애플리케이션을 빠르게 시작하기 위한 Python/FastAPI 보일러플레이트입니다.
권장 Python 버전은 `3.13+`입니다.

## 1. 빠른 시작

### 1-1. 프로젝트 초기화 (선택)

```bash
bash init.sh my-project my_project
```

### 1-2. 가상환경 및 의존성 설치

```bash
uv venv .venv
uv sync
```

### 1-3. 환경 변수 파일 생성

```bash
cp .env.sample .env
```

## 2. 서버 실행

```bash
uv run uvicorn base_template.api.main:app --host 0.0.0.0 --port 8000 --reload
```

`.env`는 설정 로더에서 자동으로 읽으므로 `--env-file .env` 옵션은 필요하지 않습니다.

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 정적 UI: `http://127.0.0.1:8000/ui`

## 3. 시스템 작동 방식

현재 Chat 시스템은 `세션 + 비동기 태스크 + 스트리밍` 구조로 동작합니다.
`src/base_template/api/chat/services`는 물리적으로 `api/` 하위에 있지만, 논리적으로 Application Service 계층이며 유스케이스 오케스트레이션을 담당합니다.

1. `POST /chat/sessions`로 세션을 생성하고 `session_id`를 받습니다.
2. `POST /chat/sessions/{session_id}/queue`로 사용자 메시지를 등록하면 `task_id`를 받습니다.
3. 등록 시점에 사용자 메시지는 DB(SQLite)와 세션 메모리에 동시에 저장됩니다.
4. Worker + ThreadPool이 태스크를 실행하고 세션 락으로 동일 `session_id`를 직렬 처리합니다.
5. 런타임(`api/chat/services/chat_runtime.py`)이 문맥을 구성하고 Graph/Node를 통해 LLM 스트리밍을 수행합니다.
6. `GET /chat/sessions/{session_id}/tasks/{task_id}/stream`으로 SSE 스트림을 받습니다.
7. 완료 후 `GET .../status`, `GET .../result`, `GET .../messages`로 상태/결과/이력을 조회합니다.
8. 정적 UI는 초기 화면 구성 시 `GET /ui-api/chat/sessions`, `GET /ui-api/chat/sessions/{session_id}/messages` 조회 API를 사용합니다.
9. 정적 UI 히스토리 항목의 삭제 버튼은 `DELETE /ui-api/chat/sessions/{session_id}`를 호출해 세션+메시지를 함께 삭제합니다.

현재 기본 구현은 In-Memory 태스크 저장소를 사용하므로, 다중 프로세스 확장은 외부 상태 저장소(예: Redis) 전환 후 적용해야 합니다.

SSE `data` 예시:

```json
{"session_id":"...","task_id":"...","type":"token","content":"안녕하세요"}
```

이벤트 타입:

- `start`
- `token`
- `done`
- `error`

상세 시퀀스/의존성은 `docs/README.md`와 `docs/chat/README.md`를 참고하세요.

### 3-1. 채팅 내역 삭제(초기화)

현재 채팅 이력은 SQLite 파일(`CHAT_DB_PATH`, 기본값: `data/db/chat/chat_history.sqlite`)에 저장됩니다.

전체 이력을 파일 단위로 초기화:

```bash
rm -f data/db/chat/chat_history.sqlite
```

SQLite 파일은 유지하고 데이터만 초기화:

```bash
sqlite3 data/db/chat/chat_history.sqlite "DELETE FROM chat_messages; DELETE FROM chat_sessions;"
```

UI 기반 삭제 API(`DELETE /ui-api/chat/sessions/{session_id}`)를 제공하며, 전체 초기화가 필요할 때는 위 파일/테이블 초기화 방식을 사용합니다.

### 3-2. Static UI 스크롤 동작 규칙

정적 UI는 메시지 스크롤 컨테이너를 `chat-cell__messages` 단일 영역으로 고정합니다.

1. 응답 스트리밍 중 사용자가 하단 근처에 있으면 자동으로 최신 토큰까지 따라 내려갑니다.
2. 사용자가 스크롤을 위로 올리면 자동 추적이 즉시 중단됩니다.
3. 사용자가 다시 하단으로 내려오면 자동 추적이 재개됩니다.
4. 스트림 수신 버퍼와 화면 표시 버퍼를 분리해 서버 chunk 크기와 UI 출력 속도를 분리합니다.
5. 스트리밍 중간 렌더에서도 마크다운/문법 강조를 즉시 반영하고, `done` 이벤트에서 최종 렌더를 확정합니다.

스크롤 이상 시 점검 순서:

1. 강력 새로고침(`Ctrl+Shift+R`)으로 정적 리소스 캐시를 제거합니다.
2. 개발자도구에서 실제 스크롤바가 `.chat-cell__messages`에 생성되는지 확인합니다.
3. 부모 컨테이너(`.chat-cell`, `.chat-grid`, `.app-body`)가 세로 스크롤을 갖지 않는지 확인합니다.

## 4. 환경 변수 설정 (`.env`)

기본 샘플은 `.env.sample`에 있습니다.

### 4-1. Chat/LLM (핵심)

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_LLM_PROVIDER` | `gemini` | `gemini`, `openai`, `echo` 중 선택 |
| `GEMINI_API_KEY` | - | Gemini API 키 |
| `GOOGLE_API_KEY` | - | Gemini 대체 키 |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini 모델명 |
| `OPENAI_API_KEY` | - | OpenAI API 키 |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI 모델명 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | Chat 이력 SQLite 파일 경로 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | 세션 메모리 최대 보관 메시지 수 |
| `CHAT_TASK_MAX_WORKERS` | `4` | Chat 태스크 워커 스레드 수 |
| `CHAT_TASK_QUEUE_MAX_SIZE` | `1000` | 태스크 큐 최대 크기 (`0`은 무제한) |
| `CHAT_TASK_STREAM_MAX_CHUNKS` | `4096` | 태스크별 스트림 버퍼 최대 청크 수 (`0`은 무제한) |
| `CHAT_TASK_RESULT_TTL_SECONDS` | `1800` | 완료/실패 태스크 결과 보관 시간(초) |
| `CHAT_TASK_MAX_STORED` | `10000` | 메모리에 유지할 태스크 최대 개수 |
| `CHAT_TASK_CLEANUP_INTERVAL_SECONDS` | `30` | 태스크 정리 주기(초) |

### 4-2. DB 통합/테스트 (선택)

| 분류 | 주요 변수 |
| --- | --- |
| PostgreSQL | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PW`, `POSTGRES_DATABASE`, `POSTGRES_DSN`, `POSTGRES_ENABLE_VECTOR` |
| MongoDB | `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_USER`, `MONGODB_PW`, `MONGODB_DB`, `MONGODB_AUTH_DB`, `MONGODB_URI` |
| Redis | `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PW`, `REDIS_URL` |
| Elasticsearch | `ELASTICSEARCH_SCHEME`, `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`, `ELASTICSEARCH_USER`, `ELASTICSEARCH_PW`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_VERIFY_CERTS`, `ELASTICSEARCH_SSL_FINGERPRINT`, `ELASTICSEARCH_HOSTS` |
| SQLite | `SQLITE_DB_DIR`, `SQLITE_DB_PATH`, `SQLITE_BUSY_TIMEOUT_MS` |

DB별 설치/실행은 `docs/intergrations/db/SETUP.md`를 참고하세요.

## 5. DB 설치 및 셋업

- 가이드: `docs/intergrations/db/SETUP.md`
- DB 통합 사용법: `docs/intergrations/db/README.md`
- 인증서 관리(Elasticsearch TLS): `certs/README.md`

## 6. 프로젝트 구조

```text
src/base_template/
  api/                  # FastAPI 라우터, HTTP DTO, API 서비스
  core/
    chat/               # 도메인 모델, 그래프, 노드
    repositories/       # 영속화 구현체, 스키마
    common/             # 도메인 공통 구성요소(메모리 저장소 등)
  integrations/         # DB/LLM 등 외부 연동
  shared/               # runtime/logging/config/exceptions
  static/               # 정적 UI
tests/                  # pytest 테스트
docs/                   # 개발 문서
```

## 7. 문서 인덱스

| 문서 | 링크 | 설명 |
| --- | --- | --- |
| 문서 허브 | [docs/README.md](docs/README.md) | 전체 아키텍처, 의존성, 개발 절차/방법 |
| Static UI 아키텍처 | [docs/static/README.md](docs/static/README.md) | 정적 UI 구조, API 연동, SSE 처리 |
| Chat 아키텍처 | [docs/chat/README.md](docs/chat/README.md) | 요청-응답 시퀀스, 상태 전이, 저장 흐름 |
| DB 통합 | [docs/intergrations/db/README.md](docs/intergrations/db/README.md) | DB 인터페이스/엔진 구현 |
| DB 설치/구성 | [docs/intergrations/db/SETUP.md](docs/intergrations/db/SETUP.md) | 로컬 DB 실행, `.env` 설정 |
| LLM 클라이언트 | [docs/intergrations/client/README.md](docs/intergrations/client/README.md) | `LLMClient` 계약, 로깅, 예외 처리 |
| Shared Runtime | [docs/shared/runtime/README.md](docs/shared/runtime/README.md) | Queue/Worker/ThreadPool 규칙 |

## 8. 테스트

```bash
uv run pytest
```

E2E(Chat, 실제 서버 기동) 예시:

```bash
uv run pytest tests/e2e/test_chat_api_server_e2e.py -v -s
```
