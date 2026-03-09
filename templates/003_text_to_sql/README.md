# Text-to-SQL Agent Template

현재 템플릿은 PostgreSQL 기반 조회 대상을 `table_allowlist.yaml`로 선언하고, startup 시 allowlist를 로드한 뒤 스키마 introspection을 수행해 채팅 런타임을 초기화합니다.  
질의 처리 흐름은 `safeguard -> context strategy -> schema selection -> raw SQL generation -> raw SQL execution -> response` 입니다.

## 1. 빠른 시작

### 1-1. 가상환경/의존성 설치

```bash
uv venv .venv
uv sync
```

### 1-2. `.env` 생성

```bash
cp .env.sample .env
```

현재 PostgreSQL 기준으로 최소한 아래 값은 채워야 합니다.

```env
GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=your-gcp-project-id
TABLE_ALLOWLIST_FILE=table_allowlist.yaml

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
```

설명:

- `GEMINI_MODEL`, `GEMINI_PROJECT`는 `safeguard`, `context_strategy`, `schema_selection`, `raw_sql_generate`, `response` 노드가 공통으로 사용합니다.
- `TABLE_ALLOWLIST_FILE`을 비우면 프로젝트 루트의 `table_allowlist.yaml` 또는 `table_allowlist.yml`을 자동 탐색합니다.
- 현재 예제는 PostgreSQL 동일 인스턴스 안의 서로 다른 database(`housing`, `population`, `ecommerce`)를 조회 대상으로 사용합니다.

### 1-3. `table_allowlist.yaml` 준비

현재 로더는 프로젝트 루트의 allowlist 파일을 읽고, `connection` 아래 직접값 또는 `*_env` 참조를 해석합니다.

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
              description: Unique sales agent code (primary key)
            - name: AGENT_NAME
              description: Sales agent name
```

중요:

- `database`와 `schema`는 allowlist에서 결정합니다.
- `host`, `port`, `user`, `password`, `database`, `schema`, `dsn`은 직접값 또는 `*_env`로 줄 수 있습니다.
- `TABLE_ALLOWLIST_FILE`로 파일을 명시하면 그 경로를 우선 사용합니다.
- 프로젝트 루트에 `table_allowlist.yaml`과 `table_allowlist.yml`이 동시에 있으면 startup 실패입니다.

DSN 기반 예시:

```yaml
connection:
  dsn_env: POSTGRES_DSN
  database: ecommerce
  schema: data
```

## 2. startup에서 실제로 일어나는 일

서버가 시작되면 아래 순서로 초기화됩니다.

1. `RuntimeEnvironmentLoader`가 프로젝트 루트 `.env`를 로드합니다.
2. `ENV` 값이 `dev/stg/prod`면 `src/text_to_sql/resources/<env>/.env`를 추가 로드합니다.
3. `table_allowlist`를 읽고 `connection.*_env`를 실제 환경 변수 값으로 치환합니다.
4. allowlist 기준으로 각 target database에 대해 schema introspection을 수행해 `schema_snapshot`을 만듭니다.
5. `QueryTargetRegistry`를 구성하고 target alias를 등록합니다.
6. 실제 DB 연결은 startup에서 선연결하지 않고, 첫 조회 시점에 lazy connect 됩니다.

즉 현재 PostgreSQL 기준으로는:

- startup 시 introspection을 위해 target별 DB 접근은 발생합니다.
- 하지만 런타임용 persistent connection은 첫 쿼리 시점에 열립니다.

## 3. 현재 PostgreSQL 기준 필수 설정 정리

### 3-1. 필수 환경 변수

| 키 | 용도 |
| --- | --- |
| `GEMINI_MODEL` | LLM 모델명 |
| `GEMINI_PROJECT` | Gemini 프로젝트 ID |
| `TABLE_ALLOWLIST_FILE` | 사용할 allowlist 파일 경로 또는 파일명 |
| `POSTGRES_HOST` | allowlist의 `host_env`가 참조할 호스트 |
| `POSTGRES_PORT` | allowlist의 `port_env`가 참조할 포트 |
| `POSTGRES_USER` | allowlist의 `user_env`가 참조할 사용자 |
| `POSTGRES_PW` | allowlist의 `password_env`가 참조할 비밀번호 |

### 3-2. 자주 같이 쓰는 선택 변수

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | 채팅 이력 SQLite 경로 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `120` | 스트림 최대 대기 시간 |
| `TEXT_TO_SQL_INTROSPECTION_MAX_WORKERS` | `4` | startup introspection 병렬 수 |
| `TEXT_TO_SQL_INTROSPECTION_SAMPLE_ROWS` | `3` | sample row 수 |
| `LOG_STDOUT` | `1` | stdout 로그 출력 여부 |

## 4. 서버 실행

```bash
uv run uvicorn text_to_sql.api.main:app --host 0.0.0.0 --port 8000 --reload
```

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 내장 UI: `http://127.0.0.1:8000/ui`

## 5. 현재 PostgreSQL 설정에서 확인할 체크리스트

서버가 기동되지 않으면 아래 순서로 확인하면 됩니다.

1. `.env`에 `GEMINI_MODEL`, `GEMINI_PROJECT`가 채워져 있는지
2. `TABLE_ALLOWLIST_FILE` 경로가 맞는지
3. `table_allowlist.yaml`의 `connection.*_env`가 실제 env 키와 일치하는지
4. allowlist의 `database`, `schema`, `tables`, `columns`가 실제 PostgreSQL 스키마와 맞는지
5. startup 로그에서 `table_allowlist 로드 완료`, `schema introspection 완료`가 보이는지

## 6. 참고 문서

- `docs/setup/env.md`
- `docs/setup/overview.md`
- `docs/core/chat.md`
- `docs/api/chat.md`
- `docs/integrations/db/query_target_registry.md`
