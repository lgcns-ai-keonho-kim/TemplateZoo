# 환경 변수 상세 레퍼런스

이 문서는 현재 코드가 실제로 읽는 환경 변수와 `.env.sample`에 남아 있는 보관/확장용 키를 구분해 설명한다.

## 1. 로딩 순서

1. `src/chatbot/api/main.py`가 시작되면 `RuntimeEnvironmentLoader().load()`를 호출한다.
2. 프로젝트 루트 `.env`를 먼저 읽는다.
3. `ENV`, `APP_ENV`, `APP_STAGE` 중 먼저 채워진 값으로 런타임 환경을 결정한다.
4. 결정된 값이 `dev`, `stg`, `prod`면 `src/chatbot/resources/<env>/.env`를 추가 로드한다.
5. 이후 import 되는 모듈은 그 시점의 값을 기준으로 초기화된다.

중요:

- `src/chatbot/resources/<env>/.env.sample`은 샘플 파일일 뿐이며 자동으로 로드되지 않는다.
- 실제 환경 파일이 필요하면 같은 위치에 `.env`를 직접 만들어야 한다.

## 2. 기본 런타임에서 실제로 읽는 키

| 변수 | 기본값 | 사용 위치 | 설명 |
| --- | --- | --- | --- |
| `ENV` | 비어 있으면 `local` | `shared/config/runtime_env_loader.py` | 런타임 환경 선택 |
| `APP_ENV` | 없음 | `shared/config/runtime_env_loader.py` | `ENV` 대체 후보 |
| `APP_STAGE` | 없음 | `shared/config/runtime_env_loader.py` | `ENV` 대체 후보 |
| `LOG_STDOUT` | `0` | `shared/logging/logger.py` | stdout JSON 로그 출력 여부 |
| `GEMINI_MODEL` | 빈 문자열 | `core/chat/nodes/response_node.py`, `safeguard_node.py` | 기본 노드 모델명 |
| `GEMINI_PROJECT` | 빈 문자열 | 동일 | Google Cloud 프로젝트 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | `core/chat/const/settings.py`, `history_repository.py` | 채팅 이력 SQLite 경로 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | `shared/chat/services/chat_service.py` | 세션 메모리 최대 메시지 수 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | `api/chat/services/runtime.py`, `service_executor.py` | 스트림 실행 제한 시간 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | `api/chat/services/runtime.py` | 완료 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | `api/chat/services/runtime.py` | 완료 저장 재시도 간격 |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | 작업 큐 최대 크기 |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | 작업 큐 poll timeout |
| `CHAT_QUEUE_MAX_SIZE` | 없음 | `api/chat/services/runtime.py` | 과거 이름 호환용 fallback 읽기 |
| `CHAT_QUEUE_POLL_TIMEOUT` | 없음 | `api/chat/services/runtime.py` | 과거 이름 호환용 fallback 읽기 |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | 이벤트 버퍼 최대 크기 |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | 이벤트 버퍼 poll timeout |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | `api/chat/services/runtime.py` | 이벤트 TTL |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | `api/chat/services/runtime.py` | 인메모리 GC 주기 |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | `api/chat/services/runtime.py` | Redis 버퍼 key prefix |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | `integrations/db/engines/sqlite/connection.py` | SQLite 잠금 대기 시간 |

## 3. 선택 확장에서 사용하는 키

| 영역 | 대표 변수 | 현재 상태 |
| --- | --- | --- |
| PostgreSQL | `POSTGRES_DSN`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PW`, `POSTGRES_DATABASE` | 주석 예시/테스트 경로 |
| MongoDB | `MONGODB_URI`, `MONGODB_HOST`, `MONGODB_PORT`, `MONGODB_USER`, `MONGODB_PW`, `MONGODB_DB`, `MONGODB_AUTH_DB` | 선택 확장 |
| Redis | `REDIS_URL`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PW` | 선택 확장 |
| Elasticsearch | `ELASTICSEARCH_HOSTS`, `ELASTICSEARCH_SCHEME`, `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`, `ELASTICSEARCH_USER`, `ELASTICSEARCH_PW`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_VERIFY_CERTS`, `ELASTICSEARCH_SSL_FINGERPRINT` | 선택 확장 |
| LanceDB | `LANCEDB_URI` | 선택 확장 |

## 4. `.env.sample`에서 주의할 점

루트 `.env.sample`에는 현재 기본 런타임이 직접 사용하지 않는 키가 남아 있다.

대표 예시:

1. `OPENAI_MODEL`, `OPENAI_API_KEY`
2. `CHAT_TASK_MAX_WORKERS`
3. `CHAT_TASK_QUEUE_MAX_SIZE`
4. `CHAT_BUFFER_BACKEND`
5. `CHAT_TASK_STREAM_MAX_CHUNKS`
6. `CHAT_TASK_RESULT_TTL_SECONDS`
7. `CHAT_TASK_MAX_STORED`
8. `CHAT_TASK_CLEANUP_INTERVAL_SECONDS`

이 값들은 샘플 보관 또는 과거 설계 흔적이지, 현재 기본 조립을 자동으로 바꾸지 않는다.

## 5. 권장 예시

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

1. 환경 변수 이름을 바꾸면 코드와 문서를 같이 수정해야 한다.
2. import 시점에 값이 고정되는 모듈이 있으므로 설정 변경 후 재시작이 필요하다.
3. 기본 런타임 키와 샘플 보관용 키를 항상 분리해서 설명해야 한다.
