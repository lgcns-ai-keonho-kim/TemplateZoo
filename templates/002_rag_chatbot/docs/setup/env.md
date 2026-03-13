# 환경 변수

## 로딩 순서

1. 프로젝트 루트 `.env`
2. `ENV`, `APP_ENV`, `APP_STAGE` 중 먼저 읽힌 값
3. 빈값이면 `local`
4. `dev/stg/prod`면 `src/rag_chatbot/resources/<env>/.env`

## 현재 직접 소비하는 핵심 키

| 변수 | 기본값 | 주요 사용 위치 |
| --- | --- | --- |
| `ENV` | `local` | `shared/config/runtime_env_loader.py` |
| `LOG_STDOUT` | `False` | `shared/logging/logger.py` |
| `GEMINI_MODEL` | 빈 문자열 | core 노드 |
| `GEMINI_PROJECT` | 빈 문자열 | core 노드, ingestion |
| `GEMINI_API_KEY` | 빈 문자열 | Gemini 모델 구성 |
| `GEMINI_EMBEDDING_MODEL` | 빈 문자열 | retrieval, ingestion |
| `GEMINI_EMBEDDING_DIM` | `1024` | retrieval, ingestion |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | core const, repository |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | `ChatService` |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | SQLite connection |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | `api/chat/services/runtime.py` |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | `api/chat/services/runtime.py` |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | `api/chat/services/runtime.py` |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | `api/chat/services/runtime.py` |
| `CHAT_QUEUE_MAX_SIZE` | `0` | 기존 키 fallback |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` |
| `CHAT_QUEUE_POLL_TIMEOUT` | `0.2` | 기존 키 fallback |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | `api/chat/services/runtime.py` |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | `api/chat/services/runtime.py` |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | `api/chat/services/runtime.py` |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | `api/chat/services/runtime.py` |
| `LANCEDB_URI` | `data/db/vector` | retrieval, ingestion |
| `POSTGRES_HOST` | `127.0.0.1` | ingestion postgres client |
| `POSTGRES_PORT` | `5432` | ingestion postgres client |
| `POSTGRES_USER` | `postgres` | ingestion postgres client |
| `POSTGRES_PW` | `postgres` | ingestion postgres client |
| `POSTGRES_DATABASE` | `playground` | ingestion postgres client |
| `POSTGRES_DSN` | 없음 | ingestion postgres client |
| `MONGODB_HOST` | `127.0.0.1` | MongoDB engine |
| `MONGODB_PORT` | `27017` | MongoDB engine |
| `MONGODB_DB` | `playground` | MongoDB engine |
| `MONGODB_URI` | 없음 | MongoDB engine |
| `REDIS_HOST` | `127.0.0.1` | Redis engine |
| `REDIS_PORT` | `6379` | Redis engine |
| `REDIS_DB` | `0` | Redis engine |
| `REDIS_URL` | 없음 | Redis engine |
| `ELASTICSEARCH_SCHEME` | `http` | ingestion elasticsearch client |
| `ELASTICSEARCH_HOST` | `127.0.0.1` | ingestion elasticsearch client |
| `ELASTICSEARCH_PORT` | `9200` | ingestion elasticsearch client |
| `ELASTICSEARCH_USER` | 없음 | ingestion elasticsearch client |
| `ELASTICSEARCH_PW` | 없음 | ingestion elasticsearch client |
| `ELASTICSEARCH_CA_CERTS` | 없음 | ingestion elasticsearch client |
| `ELASTICSEARCH_VERIFY_CERTS` | `true` | ingestion elasticsearch client |
| `ELASTICSEARCH_SSL_FINGERPRINT` | 없음 | ingestion elasticsearch client |
| `ELASTICSEARCH_HOSTS` | 없음 | ingestion elasticsearch client |

## 샘플에만 남아 있는 키

- `CHAT_TASK_MAX_WORKERS`
- `CHAT_TASK_QUEUE_MAX_SIZE`
- `CHAT_BUFFER_BACKEND`
- `CHAT_TASK_STREAM_MAX_CHUNKS`
- `CHAT_TASK_RESULT_TTL_SECONDS`
- `CHAT_TASK_MAX_STORED`
- `CHAT_TASK_CLEANUP_INTERVAL_SECONDS`

## 주의

- `.env.sample`의 예시값과 코드 기본값은 다를 수 있다.
- `ELASTICSEARCH_SCHEME`은 코드 기본값이 `http`이고, `.env.sample`은 HTTPS 예시를 담고 있다.
- import 시점에 환경 변수를 읽는 모듈이 있으므로 값을 바꾼 뒤에는 프로세스를 재시작해야 한다.
