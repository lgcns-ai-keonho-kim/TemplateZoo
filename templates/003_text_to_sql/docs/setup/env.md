# ENV 설정

현재 코드가 직접 읽는 환경 변수와 allowlist가 참조할 수 있는 연결 값을 정리합니다.

## 1. `.env` 로딩 규칙

런타임은 아래 순서로 환경 변수를 로드합니다.

1. 프로젝트 루트의 `.env`
2. `ENV`, `APP_ENV`, `APP_STAGE` 중 첫 번째로 발견한 값을 런타임 환경으로 해석
3. 해석된 값이 `dev/stg/prod`인 경우 `src/text_to_sql/resources/<env>/.env`

세 후보 키가 모두 비어 있으면 `local`로 간주합니다.

## 2. PostgreSQL 기준 최소 설정

현재 PostgreSQL 기반 target을 기동하려면 LLM 설정과 allowlist 파일, 그리고 allowlist가 참조하는 연결 값이 필요합니다.
아래 표에는 allowlist 예시에 사용한 연결 키 이름을 적었습니다. 실제 연결 키 이름은 allowlist의 `*_env` 값에 따라 달라집니다.

| 키 | 설명 | 실제 사용 위치 |
| --- | --- | --- |
| `GEMINI_MODEL` | Gemini 모델명 | `core/chat/nodes/*_node.py` |
| `GEMINI_PROJECT` | Gemini 프로젝트 ID | `core/chat/nodes/*_node.py` |
| `TABLE_ALLOWLIST_FILE` | allowlist 파일명 또는 경로. 비우면 루트 `table_allowlist.yaml/.yml` 자동 탐색 | `core/chat/utils/table_allowlist_loader.py` |
| `POSTGRES_HOST` | allowlist 예시의 `host_env` 참조값 | `table_allowlist.yaml` |
| `POSTGRES_PORT` | allowlist 예시의 `port_env` 참조값 | `table_allowlist.yaml` |
| `POSTGRES_USER` | allowlist 예시의 `user_env` 참조값 | `table_allowlist.yaml` |
| `POSTGRES_PW` | allowlist 예시의 `password_env` 참조값 | `table_allowlist.yaml` |

예시:

```env
GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=your-gcp-project-id
TABLE_ALLOWLIST_FILE=table_allowlist.yaml

POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
```

## 3. `table_allowlist`와 env의 관계

### 3-1. allowlist 파일 선택

- `TABLE_ALLOWLIST_FILE`이 있으면 그 경로를 우선 사용합니다.
- 상대경로는 프로젝트 루트 기준으로 해석합니다.
- 지정하지 않으면 루트의 `table_allowlist.yaml` 또는 `table_allowlist.yml`을 자동 탐색합니다.
- 두 파일이 동시에 존재하면 startup이 실패합니다.

### 3-2. `connection.*_env` 해석 규칙

allowlist의 `connection`은 직접값 또는 env 참조 둘 다 가능합니다.

예:

```yaml
connection:
  host_env: POSTGRES_HOST
  port_env: POSTGRES_PORT
  user_env: POSTGRES_USER
  password_env: POSTGRES_PW
  database: ecommerce
  schema: data
```

규칙:

- `host`가 있으면 직접값 사용
- `host`가 없고 `host_env`가 있으면 해당 환경 변수를 읽음
- `dsn` 또는 `dsn_env`가 있으면 host/port/user/password 대신 DSN을 우선 사용
- `database_env`, `schema_env`도 지원
- `ENV` 이름은 `POSTGRES_HOST`처럼 고정되지 않고 allowlist가 가리키는 이름을 그대로 사용
- 필수 항목의 env 값이 비어 있으면 startup 실패
- 현재 템플릿 예제는 `database`, `schema`를 allowlist 직접값으로 두는 패턴을 기본으로 사용

## 4. 현재 코드가 읽는 주요 변수

### 4-1. LLM

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `GEMINI_MODEL` | 없음 | 모델명 |
| `GEMINI_PROJECT` | 없음 | 프로젝트 ID |
| `GEMINI_API_KEY` | 없음 | SDK/런타임 환경에서 사용할 수 있는 인증용 키. 애플리케이션 코드가 직접 검증하지는 않음 |

### 4-2. Chat 런타임

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | 채팅 이력 SQLite 경로 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | 세션 메모리 최대 메시지 수 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `120` | 스트림 최대 대기 시간(초) |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | assistant 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | assistant 저장 재시도 간격(초) |

### 4-3. 큐 / 이벤트 버퍼

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | 작업 큐 최대 크기 |
| `CHAT_QUEUE_MAX_SIZE` | `0` | 작업 큐 fallback 키 |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | 작업 큐 poll 대기 시간 |
| `CHAT_QUEUE_POLL_TIMEOUT` | `0.2` | 작업 큐 poll fallback 키 |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | 이벤트 버퍼 최대 크기 |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | 이벤트 버퍼 poll 대기 시간 |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | 이벤트 버퍼 TTL |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | 인메모리 이벤트 GC 주기 |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | Redis 이벤트 키 prefix |

### 4-4. Assistant context cache

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `CHAT_ASSISTANT_CONTEXT_BACKEND` | `in_memory` | `in_memory` 또는 `redis` |
| `CHAT_ASSISTANT_CONTEXT_TTL_SECONDS` | `1800` | 컨텍스트 TTL |
| `CHAT_ASSISTANT_CONTEXT_MAX_SESSIONS` | `2000` | 최대 세션 수 |
| `CHAT_ASSISTANT_CONTEXT_REDIS_KEY_PREFIX` | `chat:assistant_ctx` | Redis 키 prefix |
| `CHAT_ASSISTANT_CONTEXT_REDIS_LRU_INDEX_KEY` | `chat:assistant_ctx:lru` | Redis LRU 인덱스 키 |

### 4-5. Text-to-SQL startup

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `TABLE_ALLOWLIST_FILE` | 자동 탐색 | allowlist 파일 경로 |
| `TEXT_TO_SQL_INTROSPECTION_MAX_WORKERS` | `4` | startup introspection 병렬 수 |
| `TEXT_TO_SQL_INTROSPECTION_SAMPLE_ROWS` | `3` | sample row 수 |

### 4-6. SQLite

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | SQLite lock 대기 시간(ms) |

### 4-7. Redis

`CHAT_ASSISTANT_CONTEXT_BACKEND=redis`일 때 필요합니다.

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `REDIS_HOST` | `127.0.0.1` | 호스트 |
| `REDIS_PORT` | `6379` | 포트 |
| `REDIS_DB` | `0` | DB 인덱스 |
| `REDIS_PW` | 없음 | 비밀번호 |

### 4-8. MongoDB

현재 PostgreSQL 기준 기동에는 필요하지 않지만, MongoDB target을 선언하고 allowlist에서 `*_env`를 참조하면 아래와 같은 이름을 사용할 수 있습니다.
아래 키 이름도 allowlist 예시에 맞춘 값이며, 실제 이름은 allowlist의 `*_env` 설정에 따라 달라집니다.

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `MONGODB_HOST` | `127.0.0.1` | allowlist 예시의 `host_env` 참조값 |
| `MONGODB_PORT` | `27017` | allowlist 예시의 `port_env` 참조값 |
| `MONGODB_USER` | 없음 | allowlist 예시의 `user_env` 참조값 |
| `MONGODB_PW` | 없음 | allowlist 예시의 `password_env` 참조값 |
| `MONGODB_AUTH_DB` | 없음 | allowlist 예시의 `auth_source_env` 참조값 |
| `MONGODB_URI` | 없음 | allowlist 예시의 `dsn_env` 참조값 |

## 5. startup에서 실제로 검증되는 것

서버가 시작되면 아래가 바로 검증됩니다.

1. allowlist 파일 존재 여부
2. allowlist YAML 형식
3. `connection.*_env`가 가리키는 환경 변수 값 존재 여부
4. allowlist target별 schema introspection 가능 여부
5. allowlist의 테이블/컬럼이 실제 DB와 맞는지

즉 `.env` 값이 비어 있거나, allowlist와 실제 PostgreSQL 스키마가 다르면 startup 단계에서 바로 실패합니다.
