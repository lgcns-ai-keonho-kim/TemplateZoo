# Text-to-SQL Agent Template

LLM 기반 Text-to-SQL 애플리케이션을 빠르게 시작하기 위한 Python/FastAPI 템플릿이다.
권장 Python 버전은 `3.13+`이다.

현재 템플릿은 `table_allowlist.yaml`에 선언한 조회 대상과 startup 시점 schema introspection 결과를 기반으로, `safeguard -> context strategy -> schema selection -> raw SQL generation -> raw SQL execution -> response` 파이프라인을 실행한다.

## 1. 빠른 시작

### 1-1. 가상환경/의존성 설치

```bash
uv venv .venv
uv sync
```

### 1-2. 환경 변수 파일 생성

기본 로컬 실행:

```bash
cp .env.sample .env
```

현재 기본 그래프는 Gemini 설정과 PostgreSQL allowlist를 사용한다.

```env
ENV=local
GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=your-gcp-project-id
GEMINI_API_KEY=
TABLE_ALLOWLIST_FILE=table_allowlist.yaml

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
```

런타임 환경이 `dev/stg/prod`인 경우에는 루트 `.env` 외에 환경별 리소스 파일도 준비해야 한다.

예시(`dev`):

```bash
cp src/text_to_sql/resources/dev/.env.sample src/text_to_sql/resources/dev/.env
```

`RuntimeEnvironmentLoader`는 아래 순서로 환경을 로드한다.

1. 프로젝트 루트 `.env`
2. `ENV` / `APP_ENV` / `APP_STAGE` 해석
3. 필요 시 `src/text_to_sql/resources/<env>/.env`

### 1-3. `table_allowlist.yaml` 준비

현재 로더는 프로젝트 루트의 allowlist 파일을 읽고, `connection` 아래 직접값 또는 `*_env` 참조를 해석한다.

PostgreSQL 예시:

```yaml
version: 1

targets:
  - alias: ecommerce
    engine: postgres
    connection:
      host_env: POSTGRES_HOST
      port_env: POSTGRES_PORT
      user_env: POSTGRES_USER
      password_env: POSTGRES_PW
      database: ecommerce
      schema: data
    allowlist:
      tables:
        - name: AGENTS
          description: Sales agent master information
          columns:
            - name: AGENT_CODE
              description: Unique sales agent code
            - name: AGENT_NAME
              description: Sales agent name
```

중요:

- `TABLE_ALLOWLIST_FILE`을 비우면 프로젝트 루트의 `table_allowlist.yaml` 또는 `table_allowlist.yml`을 자동 탐색한다.
- `database`, `schema`, `tables`, `columns`는 allowlist에서 결정한다.
- `host`, `port`, `user`, `password`, `database`, `schema`, `dsn`은 직접값 또는 `*_env`로 줄 수 있다.
- 프로젝트 루트에 `table_allowlist.yaml`과 `table_allowlist.yml`이 동시에 있으면 startup 실패다.

### 1-4. 서버 실행

```bash
uv run uvicorn text_to_sql.api.main:app --host 0.0.0.0 --port 8000 --reload
```

startup 시 실제로 수행되는 순서:

1. 루트 `.env`와 환경별 `.env`를 로드한다.
2. `table_allowlist`를 읽고 `connection.*_env`를 실제 환경 변수 값으로 치환한다.
3. allowlist 기준으로 각 target database에 대해 schema introspection을 수행해 `schema_snapshot`을 만든다.
4. `QueryTargetRegistry`를 구성하고 target alias를 등록한다.
5. 런타임용 DB 연결은 startup에서 선연결하지 않고, 첫 조회 시점에 lazy connect 된다.

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 정적 UI: `http://127.0.0.1:8000/ui`

## 2. API 인터페이스 요약

### 2-1. Chat API

| Method | Path | 상태코드 | 설명 |
| --- | --- | --- | --- |
| `POST` | `/chat` | `202` | 채팅 작업 제출 (`session_id`, `message`, `context_window`) |
| `GET` | `/chat/{session_id}` | `200` | 세션 스냅샷(메시지/최근 상태) 조회 |
| `GET` | `/chat/{session_id}/events?request_id=...` | `200` | 요청 단위 SSE 이벤트 구독 |

### 2-2. UI API

| Method | Path | 상태코드 | 설명 |
| --- | --- | --- | --- |
| `POST` | `/ui-api/chat/sessions` | `201` | UI 세션 생성 |
| `GET` | `/ui-api/chat/sessions` | `200` | UI 세션 목록 |
| `GET` | `/ui-api/chat/sessions/{session_id}/messages` | `200` | UI 메시지 목록 |
| `DELETE` | `/ui-api/chat/sessions/{session_id}` | `200` | 세션+메시지 삭제 |

### 2-3. Health API

| Method | Path | 상태코드 | 설명 |
| --- | --- | --- | --- |
| `GET` | `/health` | `200` | 서버 생존 상태 확인 |

## 3. 동작 방식

현재 시스템은 `세션 + 비동기 실행 + SSE + Raw SQL 파이프라인` 구조로 동작한다.

1. UI는 `/ui-api/chat/sessions`로 세션 목록을 가져오고 활성 세션을 정한다.
2. 사용자가 메시지를 보내면 `POST /chat`을 호출한다.
3. 서버는 `session_id`, `request_id`, `status=QUEUED`를 즉시 반환한다.
4. UI는 `GET /chat/{session_id}/events?request_id=...`로 스트림을 구독한다.
5. `ServiceExecutor`가 작업 큐를 소비하며 `start -> sql_plan/sql_result/token -> done/error` 이벤트를 보낸다.
6. `ChatService`는 사용자 메시지 저장, 그래프 실행, assistant 응답 영속화를 담당한다.
7. 그래프는 `safeguard -> context strategy -> schema selection -> raw SQL generation -> raw SQL execution -> response` 순서로 진행한다.
8. SQL 실행 성공 결과는 `answer_source_meta`로 저장되어 후속 설명 질의에 재사용된다.
9. 완료 시 assistant 응답은 `request_id` 멱등 기준으로 1회만 저장된다.
10. 필요하면 `GET /chat/{session_id}`로 최종 스냅샷을 조회한다.

SSE `data` 예시:

```json
{
  "session_id": "...",
  "request_id": "...",
  "type": "sql_result",
  "node": "raw_sql_execute",
  "content": "...",
  "status": null,
  "error_message": null,
  "metadata": {}
}
```

이벤트 타입:

- `start`
- `token`
- `sql_plan`
- `sql_result`
- `done`
- `error`

## 4. 환경 변수 (`.env`)

기본 샘플: `.env.sample`

전체 키 상세 설명과 로딩 우선순위는 `docs/setup/env.md`를 참고한다.

### 4-1. 런타임/로그

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ENV` | (빈값) | `local/dev/stg/prod` 런타임 선택 |
| `TABLE_ALLOWLIST_FILE` | `table_allowlist.yaml` | 사용할 allowlist 파일 경로 또는 파일명 |
| `LOG_STDOUT` | `1` | stdout 로그 출력 여부 |

### 4-2. LLM

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `GEMINI_MODEL` | - | 기본 채팅 노드에서 사용할 모델명 |
| `GEMINI_PROJECT` | - | Google Cloud 프로젝트 식별자 |
| `GEMINI_API_KEY` | - | Gemini 인증에 사용하는 API 키 |

### 4-3. Chat 실행/저장

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | Chat 이력 SQLite 경로 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | 세션 메모리 최대 메시지 수 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `120` | SSE 대기/실행 타임아웃 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | 완료 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | 완료 저장 재시도 간격(초) |

### 4-4. 큐 / 이벤트 버퍼

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | 작업 큐 최대 크기 (`0` 무제한) |
| `CHAT_QUEUE_MAX_SIZE` | `0` | 작업 큐 fallback 키 |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | 작업 큐 poll timeout(초) |
| `CHAT_QUEUE_POLL_TIMEOUT` | `0.2` | 작업 큐 poll fallback 키 |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | 이벤트 버퍼 최대 크기 (`0` 무제한) |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | 이벤트 버퍼 pop timeout(초) |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | 이벤트 버퍼 TTL(초) |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | 인메모리 버퍼 GC 주기(초) |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | Redis 이벤트 키 prefix |

### 4-5. Assistant context cache

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_ASSISTANT_CONTEXT_BACKEND` | `in_memory` | `in_memory` 또는 `redis` |
| `CHAT_ASSISTANT_CONTEXT_TTL_SECONDS` | `1800` | 마지막 assistant 컨텍스트 TTL |
| `CHAT_ASSISTANT_CONTEXT_MAX_SESSIONS` | `2000` | 캐시 최대 세션 수 |
| `CHAT_ASSISTANT_CONTEXT_REDIS_KEY_PREFIX` | `chat:assistant_ctx` | Redis 키 prefix |
| `CHAT_ASSISTANT_CONTEXT_REDIS_LRU_INDEX_KEY` | `chat:assistant_ctx:lru` | Redis LRU 인덱스 키 |

### 4-6. Text-to-SQL startup

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `TEXT_TO_SQL_INTROSPECTION_MAX_WORKERS` | `4` | startup introspection 병렬 수 |
| `TEXT_TO_SQL_INTROSPECTION_SAMPLE_ROWS` | `3` | table sample row 수 |

### 4-7. PostgreSQL 필수값

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `POSTGRES_HOST` | `127.0.0.1` | allowlist `host_env` 참조 호스트 |
| `POSTGRES_PORT` | `5432` | allowlist `port_env` 참조 포트 |
| `POSTGRES_USER` | `postgres` | allowlist `user_env` 참조 사용자 |
| `POSTGRES_PW` | `postgres` | allowlist `password_env` 참조 비밀번호 |

### 4-8. 선택값

Redis:

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `REDIS_HOST` | `127.0.0.1` | Redis 호스트 |
| `REDIS_PORT` | `6379` | Redis 포트 |
| `REDIS_DB` | `0` | Redis DB 인덱스 |
| `REDIS_PW` | - | Redis 비밀번호 |

MongoDB:

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `MONGODB_HOST` | `127.0.0.1` | MongoDB 호스트 |
| `MONGODB_PORT` | `27017` | MongoDB 포트 |
| `MONGODB_USER` | - | MongoDB 사용자 |
| `MONGODB_PW` | - | MongoDB 비밀번호 |
| `MONGODB_AUTH_DB` | - | 인증 DB |
| `MONGODB_URI` | - | MongoDB URI 직접 지정 |

기타:

- `.env.sample`에는 Elasticsearch, SQLite 관련 키도 포함되어 있다.
- `ENV=dev/stg/prod`를 사용할 때는 `src/text_to_sql/resources/<env>/.env`가 추가로 필요하다.
- 설정 값은 import 시점에 고정 반영되는 모듈이 있으므로 변경 후 프로세스를 재시작해야 한다.

## 5. 채팅 이력 초기화

기본 저장소는 SQLite(`CHAT_DB_PATH`)다.

전체 파일 초기화:

```bash
rm -f data/db/chat/chat_history.sqlite
```

테이블 데이터만 삭제:

```bash
sqlite3 data/db/chat/chat_history.sqlite "DELETE FROM chat_messages; DELETE FROM chat_sessions; DELETE FROM chat_request_commits;"
```

## 6. 프로젝트 구조

### 6-1. 최상위 구조

```text
.
  src/text_to_sql/
    api/                # HTTP 진입점, DTO, DI 조립
    core/               # Text-to-SQL 도메인 규칙과 그래프 조립
    shared/             # 공통 실행 인프라와 재사용 컴포넌트
    integrations/       # 외부 시스템 연동 어댑터
    resources/          # 런타임 환경별 리소스 파일
    static/             # 정적 UI 리소스
  tests/                # pytest 테스트
  docs/                 # 코드 기준 상세 문서
  data/                 # 기본 로컬 실행 데이터 경로
```

### 6-2. `src/text_to_sql/` 디렉터리 레벨 책임 맵

| 경로 | 역할 | 구현 책임 범위 | 책임 밖 범위 |
| --- | --- | --- | --- |
| `src/text_to_sql/api` | FastAPI 진입 계층 | 라우터 등록, 요청/응답 모델, HTTP 예외 변환, 런타임 의존성 주입 | 도메인 규칙 자체, DB 엔진 세부 구현 |
| `src/text_to_sql/core` | Text-to-SQL 도메인 계층 | 상태 모델, 프롬프트, 노드 조립, 그래프 분기 규칙 | HTTP 프로토콜, 큐/버퍼 인프라 운영 |
| `src/text_to_sql/shared` | 공용 실행 계층 | 서비스 오케스트레이션, 저장소, 메모리, 런타임 유틸리티, 공통 예외/로깅/설정 | 특정 외부 제품 API 세부 구현 |
| `src/text_to_sql/integrations` | 외부 연동 계층 | LLM/DB/파일 시스템/임베딩 어댑터, 연결/매퍼/엔진 | Text-to-SQL 유스케이스 정책, API 라우팅 |
| `src/text_to_sql/resources` | 환경 리소스 계층 | `dev/stg/prod`별 `.env` 샘플과 환경 파일 보관 | 런타임 로직 |
| `src/text_to_sql/static` | 웹 UI 정적 리소스 계층 | HTML/CSS/JS, 아이콘, 프런트 상태 처리 | FastAPI 비즈니스 로직, 도메인 정책 |

### 6-3. `src/text_to_sql/api` 하위 구조

```text
src/text_to_sql/api/
  main.py               # 앱 엔트리, /ui 마운트, lifespan startup/shutdown
  const/                # API prefix/path/tag 상수
  chat/                 # 비동기 Chat API
  ui/                   # UI 전용 세션/메시지 API
  health/               # 서버 상태 확인 API
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/text_to_sql/api/chat/models` | Chat DTO | `/chat` 요청/응답 검증, SSE 구독 입력/출력 모델 |
| `src/text_to_sql/api/chat/routers` | Chat 라우터 | 작업 제출, 스트림 구독, 세션 스냅샷 조회 |
| `src/text_to_sql/api/chat/services` | Chat 런타임 조립 | `ChatService`, `ServiceExecutor`, 큐/버퍼 싱글턴 조립 |
| `src/text_to_sql/api/chat/utils` | Chat API 보조 유틸 | 도메인 모델을 API 응답 형태로 변환 |
| `src/text_to_sql/api/ui/models` | UI DTO | 세션/메시지 목록 응답 모델 |
| `src/text_to_sql/api/ui/routers` | UI 라우터 | 세션 생성, 조회, 삭제 엔드포인트 |
| `src/text_to_sql/api/ui/services` | UI 서비스 | `ChatService` 결과를 UI 응답 모델로 매핑 |
| `src/text_to_sql/api/ui/utils` | UI 매퍼 | 도메인 엔티티를 UI DTO로 변환 |
| `src/text_to_sql/api/health` | Health API | `/health` 단일 엔드포인트와 응답 모델 관리 |

### 6-4. `src/text_to_sql/core/chat` 하위 구조

```text
src/text_to_sql/core/chat/
  const/                # 도메인 상수와 기본 메시지
  models/               # ChatSession, ChatMessage 같은 엔티티
  state/                # 그래프 상태 키 정의
  prompts/              # 시스템 프롬프트
  nodes/                # safeguard/context/raw SQL/response 노드 조립체
  graphs/               # LangGraph 그래프 조립
  utils/                # allowlist 로드, introspection, 매핑 유틸
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/text_to_sql/core/chat/const` | 도메인 설정값 | 컬렉션명, 페이지 크기, 기본 문맥 길이, 분기 상수 |
| `src/text_to_sql/core/chat/models` | 핵심 엔티티 | 세션, 메시지, 역할, 상태 모델 정의 |
| `src/text_to_sql/core/chat/state` | 그래프 상태 계약 | 노드 간 전달되는 상태 키의 타입 계약 |
| `src/text_to_sql/core/chat/prompts` | 프롬프트 정책 | safeguard, context strategy, schema selection, SQL generation, response 프롬프트 |
| `src/text_to_sql/core/chat/nodes` | 도메인 노드 조립 | 실제 사용할 LLM/분기/실행/메시지 노드 인스턴스 선언 |
| `src/text_to_sql/core/chat/graphs` | 그래프 정의 | 노드 연결, 진입점, 조건 분기, stream 정책 설정 |
| `src/text_to_sql/core/chat/utils` | 런타임 준비 유틸 | allowlist 로드, schema introspection, 도메인 매핑 지원 |

### 6-5. `src/text_to_sql/shared` 하위 구조

```text
src/text_to_sql/shared/
  chat/                 # 그래프 실행, 저장소, 메모리, 서비스
  runtime/              # 큐, 이벤트 버퍼, 워커, 스레드풀
  config/               # 설정/런타임 환경 로더
  logging/              # 공통 로거와 로그 저장소
  exceptions/           # 공통 예외 모델
  const/                # 공통 상수
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/text_to_sql/shared/chat/interface` | 포트 계약 | 그래프, 서비스, 실행기 인터페이스 정의 |
| `src/text_to_sql/shared/chat/graph` | 그래프 공통 실행기 | 그래프 컴파일, 이벤트 표준화, stream 필터링 |
| `src/text_to_sql/shared/chat/nodes` | 재사용 노드 | LLMNode, BranchNode, MessageNode, RawSQLExecutor 같은 범용 노드 |
| `src/text_to_sql/shared/chat/repositories` | 대화 이력 저장소 | 세션/메시지 CRUD, request_id 멱등 저장 관리 |
| `src/text_to_sql/shared/chat/memory` | 세션 메모리 캐시 | 최근 메시지 컨텍스트 메모리 유지 |
| `src/text_to_sql/shared/chat/runtime` | 런타임 상태 저장소 | query target registry, assistant context store 관리 |
| `src/text_to_sql/shared/chat/services` | 서비스 계층 | `ChatService`, `ServiceExecutor` 실행 오케스트레이션 |
| `src/text_to_sql/shared/runtime` | 실행 인프라 | Queue, EventBuffer, Worker, ThreadPool 제공 |
| `src/text_to_sql/shared/config` | 설정 로딩 | `.env`/JSON/환경 변수 병합 및 런타임 환경 해석 |
| `src/text_to_sql/shared/logging` | 공통 로깅 | Logger, 로그 모델, 저장소 구현 |
| `src/text_to_sql/shared/exceptions` | 공통 예외 | 코드/원인 추적이 가능한 애플리케이션 예외 정의 |

### 6-6. `src/text_to_sql/integrations` 하위 구조

```text
src/text_to_sql/integrations/
  llm/                  # LLM 클라이언트 래퍼
  db/                   # DB 클라이언트, 엔진, 쿼리 빌더
  fs/                   # 파일 시스템 저장소
  embedding/            # 임베딩 클라이언트
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/text_to_sql/integrations/llm` | LLM 연동 | LangChain 모델 래핑, 호출 로깅, 예외 표준화 |
| `src/text_to_sql/integrations/db/base` | DB 공통 타입 | 엔진/세션/모델/쿼리 계약 |
| `src/text_to_sql/integrations/db/query_builder` | 쿼리 빌더 | 읽기/쓰기/삭제 쿼리 조립 유틸 |
| `src/text_to_sql/integrations/db/engines/sqlite` | SQLite 엔진 | 기본 Chat 저장소 엔진 |
| `src/text_to_sql/integrations/db/engines/postgres` | PostgreSQL 엔진 | 관계형 조회 및 벡터 저장소 지원 |
| `src/text_to_sql/integrations/db/engines/mongodb` | MongoDB 엔진 | 문서 저장/조회 어댑터 |
| `src/text_to_sql/integrations/db/engines/redis` | Redis 엔진 | keyspace 기반 저장/벡터 유틸 |
| `src/text_to_sql/integrations/db/engines/elasticsearch` | Elasticsearch 엔진 | 인덱스 기반 검색 어댑터 |
| `src/text_to_sql/integrations/db/engines/lancedb` | LanceDB 엔진 | 로컬 벡터 저장소 지원 |
| `src/text_to_sql/integrations/fs` | 파일 시스템 연동 | 파일 저장소 계약과 로컬 파일 엔진 구현 |
| `src/text_to_sql/integrations/embedding` | 임베딩 연동 | 임베딩 모델 호출 래퍼 |

### 6-7. `src/text_to_sql/resources`, `static`

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/text_to_sql/resources/dev` | 개발 환경 리소스 | `ENV=dev`일 때 사용할 `.env.sample` 및 환경 파일 보관 |
| `src/text_to_sql/resources/stg` | 스테이징 환경 리소스 | `ENV=stg`용 샘플/설정 보관 |
| `src/text_to_sql/resources/prod` | 운영 환경 리소스 | `ENV=prod`용 샘플/설정 보관 |
| `src/text_to_sql/static/index.html` | UI 엔트리 | 채팅 화면 골격 |
| `src/text_to_sql/static/css` | 스타일 | 레이아웃/테마 정의 |
| `src/text_to_sql/static/js/core` | 프런트 초기화 | 앱 부트스트랩과 전역 흐름 제어 |
| `src/text_to_sql/static/js/chat` | 채팅 UI | 전송, 셀 렌더링, 스트림 반영 |
| `src/text_to_sql/static/js/ui` | UI 제어 | 패널 토글, 그리드, 테마 관리 |
| `src/text_to_sql/static/js/utils` | 프런트 유틸 | DOM, Markdown, 문법 하이라이팅 |
| `src/text_to_sql/static/asset` | 정적 자산 | 아이콘, 로고 등 시각 리소스 |

## 7. 계층 경계

1. `api`는 HTTP 입출력 경계만 다루고, Text-to-SQL 규칙은 직접 구현하지 않는다.
2. `core`는 Text-to-SQL 정책과 그래프 분기를 정의하지만, 큐/버퍼/DB 연결 세부 구현은 모른다.
3. `shared`는 `core`를 실제 서비스로 실행하기 위한 공통 실행기와 저장소를 제공한다.
4. `integrations`는 외부 기술 스택을 감싸지만, 어떤 유스케이스에서 호출할지는 결정하지 않는다.
5. `static`은 `/ui-api/chat/*`, `/chat/*`를 소비하는 클라이언트이며 서버 정책의 소유자가 아니다.

## 8. 관련 문서

| 문서 | 링크 | 설명 |
| --- | --- | --- |
| 문서 허브 | [docs/README.md](docs/README.md) | 전체 맵, 변경 진입점 |
| Setup 개요 | [docs/setup/overview.md](docs/setup/overview.md) | 인프라/환경 문서 인덱스 |
| Setup ENV | [docs/setup/env.md](docs/setup/env.md) | `.env` 키 전체 설명, 로딩 순서 |
| Setup MongoDB | [docs/setup/mongodb.md](docs/setup/mongodb.md) | MongoDB 설치/연동 |
| Setup FileSystem | [docs/setup/filesystem.md](docs/setup/filesystem.md) | 파일 시스템 로그 연동 |
| API 개요 | [docs/api/overview.md](docs/api/overview.md) | API 계층 책임/라우팅 |
| API Chat | [docs/api/chat.md](docs/api/chat.md) | `/chat` 인터페이스, SSE |
| API UI | [docs/api/ui.md](docs/api/ui.md) | `/ui-api/chat` 인터페이스 |
| API Health | [docs/api/health.md](docs/api/health.md) | `/health` 인터페이스 |
| Core 개요 | [docs/core/overview.md](docs/core/overview.md) | core 계층 문서 인덱스 |
| Core Chat | [docs/core/chat.md](docs/core/chat.md) | 그래프/노드 동작 |
| Shared 개요 | [docs/shared/overview.md](docs/shared/overview.md) | shared 계층 문서 인덱스 |
| Shared Chat | [docs/shared/chat/README.md](docs/shared/chat/README.md) | 실행기/저장/멱등 |
| Shared Runtime | [docs/shared/runtime.md](docs/shared/runtime.md) | Queue/EventBuffer 구성 |
| Shared Config | [docs/shared/config.md](docs/shared/config.md) | 설정/환경 로딩 |
| Shared Exceptions | [docs/shared/exceptions.md](docs/shared/exceptions.md) | 공통 예외 구조 |
| Shared Logging | [docs/shared/logging.md](docs/shared/logging.md) | 로깅/저장소 구성 |
| Integrations 개요 | [docs/integrations/overview.md](docs/integrations/overview.md) | 연동 계층 문서 인덱스 |
| Integrations DB | [docs/integrations/db/README.md](docs/integrations/db/README.md) | DB 엔진/쿼리 빌더 문서 인덱스 |
| Integrations LLM | [docs/integrations/llm/README.md](docs/integrations/llm/README.md) | `LLMClient` 사용 |
| Integrations FS | [docs/integrations/fs/README.md](docs/integrations/fs/README.md) | 파일 저장소 경로/정책 |
| Integrations Embedding | [docs/integrations/embedding/README.md](docs/integrations/embedding/README.md) | 임베딩 연동 모듈 |
| Query Target Registry | [docs/integrations/db/query_target_registry.md](docs/integrations/db/query_target_registry.md) | allowlist target 등록/조회 |
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

정적 분석 예시:

```bash
uv run ty check src
uv run ruff format src -v
uv run ruff clean
```
