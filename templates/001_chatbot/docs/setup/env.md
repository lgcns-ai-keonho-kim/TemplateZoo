# 환경 변수 상세 레퍼런스

이 문서는 현재 코드가 실제로 읽는 환경 변수와, `.env.sample` 및 `src/chatbot/resources/*` 샘플에 남아 있는 선택/보관용 키를 구분해 설명한다.

## 1. 로딩 순서

1. `src/chatbot/api/main.py`가 시작되면 `RuntimeEnvironmentLoader().load()`를 호출한다.
2. 프로젝트 루트 `.env`를 먼저 읽는다.
3. `ENV`, `APP_ENV`, `APP_STAGE` 중 먼저 채워진 값으로 런타임 환경을 결정한다.
4. 결정된 값이 `dev`, `stg`, `prod`면 `src/chatbot/resources/<env>/.env`를 추가 로드한다.
5. 그 이후 import 되는 모듈은 해당 환경 값을 고정해서 사용한다.

## 2. 기본 런타임에서 실제로 읽는 키

| 변수 | 기본값 | 사용 위치 | 설명 |
| --- | --- | --- | --- |
| `ENV` | 비어 있으면 `local` | `shared/config/runtime_env_loader.py` | 런타임 환경 선택 |
| `APP_ENV` | 없음 | `shared/config/runtime_env_loader.py` | `ENV` 대체 후보 |
| `APP_STAGE` | 없음 | `shared/config/runtime_env_loader.py` | `ENV` 대체 후보 |
| `LOG_STDOUT` | `0` 계열 기본 | `shared/logging/logger.py` | stdout JSON 로그 출력 여부 |
| `GEMINI_MODEL` | 없음 | `core/chat/nodes/response_node.py`, `safeguard_node.py` | 기본 노드 모델명 |
| `GEMINI_PROJECT` | 없음 | 동일 | Google Cloud 프로젝트 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | `core/chat/const/settings.py`, `history_repository.py` | 채팅 이력 SQLite 파일 경로 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | `shared/chat/services/chat_service.py` | 세션 메모리 최대 메시지 수 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | `api/chat/services/runtime.py` | 스트림 전체 타임아웃 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | `api/chat/services/runtime.py` | 완료 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | `api/chat/services/runtime.py` | 완료 저장 재시도 간격 |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | 작업 큐 최대 크기 |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | 작업 큐 poll timeout |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | 이벤트 버퍼 최대 크기 |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | 이벤트 버퍼 pop timeout |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | `api/chat/services/runtime.py` | 이벤트 TTL |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | `api/chat/services/runtime.py` | 인메모리 GC 주기 |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | `api/chat/services/runtime.py` | Redis 버퍼 키 prefix |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | `integrations/db/engines/sqlite/connection.py` | SQLite 잠금 대기 시간 |

## 3. 선택 확장에서 사용하는 키

| 영역 | 대표 변수 | 현재 상태 |
| --- | --- | --- |
| PostgreSQL | `POSTGRES_DSN`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PW`, `POSTGRES_DATABASE` | 예시 조립 경로만 존재 |
| MongoDB | `MONGODB_URI`, `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_USER`, `MONGODB_PW`, `MONGODB_DB`, `MONGODB_AUTH_DB` | 선택 확장 |
| Redis | `REDIS_URL`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PW` | 선택 확장 |
| Elasticsearch | `ELASTICSEARCH_HOSTS`, `ELASTICSEARCH_SCHEME`, `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`, `ELASTICSEARCH_USER`, `ELASTICSEARCH_PW`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_VERIFY_CERTS`, `ELASTICSEARCH_SSL_FINGERPRINT` | 선택 확장 |
| LanceDB | `LANCEDB_URI` | 선택 확장 |

## 4. `.env.sample`과 리소스 샘플에서 주의할 점

1. 루트 `.env.sample`에는 `OPENAI_*`, `CHAT_TASK_*`, `CHAT_BUFFER_BACKEND`, `CHAT_TASK_STREAM_MAX_CHUNKS` 같은 키가 남아 있지만 현재 기본 런타임은 직접 사용하지 않는다.
2. `src/chatbot/resources/dev|stg|prod/.env.sample`은 샘플 파일이므로, 해당 환경을 실제로 쓰려면 같은 위치에 `.env` 파일을 따로 만들어야 한다.
3. 리소스 샘플의 `CHAT_LLM_PROVIDER`, `OPENAI_MODEL`은 예시 성격이며 현재 기본 노드 조립에는 연결돼 있지 않다.

## 5. 권장 작성 예시

### 5-1. 로컬 기본 실행

```env
ENV=local
LOG_STDOUT=1
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_PROJECT=your-project
GEMINI_API_KEY=
CHAT_DB_PATH=data/db/chat/chat_history.sqlite
CHAT_MEMORY_MAX_MESSAGES=200
CHAT_STREAM_TIMEOUT_SECONDS=180
CHAT_PERSIST_RETRY_LIMIT=2
CHAT_PERSIST_RETRY_DELAY_SECONDS=0.5
CHAT_JOB_QUEUE_MAX_SIZE=0
CHAT_JOB_QUEUE_POLL_TIMEOUT=0.2
CHAT_EVENT_BUFFER_MAX_SIZE=0
CHAT_EVENT_BUFFER_POLL_TIMEOUT=0.2
CHAT_EVENT_BUFFER_TTL_SECONDS=600
CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS=30
CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX=chat:stream
SQLITE_BUSY_TIMEOUT_MS=5000
```

### 5-2. 환경별 리소스 파일 준비

```bash
cp src/chatbot/resources/dev/.env.sample src/chatbot/resources/dev/.env
```

## 6. 유지보수 포인트

1. 환경 변수 이름을 바꾸면 코드만이 아니라 setup 문서와 README를 함께 수정해야 한다.
2. import 시점에 값이 고정되는 모듈이 있으므로, 설정 변경 후 재시작 필요 여부를 문서에 명시해야 한다.
3. 기본 런타임이 읽는 키와 샘플에 남아 있는 보관용 키를 항상 분리해서 설명해야 한다.

## 7. 추가 개발과 확장 시 주의점

1. 새 공급자나 새 큐 백엔드를 추가하더라도, 기본 런타임 조립이 바뀌지 않았다면 문서상 기본값을 바꾸면 안 된다.
2. 환경별 파일을 늘릴 때는 `RuntimeEnvironmentLoader._SUPPORTED_ENVS`와 리소스 디렉터리를 함께 수정해야 한다.
3. 선택 확장 키를 기본 런타임 표에 섞어 쓰면 운영자가 잘못된 키를 입력하기 쉬워진다.

## 8. 관련 문서

- `docs/setup/sqlite.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/setup/lancedb.md`
- `docs/setup/troubleshooting.md`
