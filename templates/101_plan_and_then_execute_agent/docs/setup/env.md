# 환경 변수 상세 설명

이 문서는 `.env.sample` 선언값과 코드 소비 지점을 함께 정리한 환경 변수 사전입니다.

## 1. 로딩 순서

`RuntimeEnvironmentLoader` 기준:

1. 프로젝트 루트 `.env` 로드
2. `ENV`/`APP_ENV`/`APP_STAGE`로 런타임 환경 결정
3. 값이 비어 있으면 `local`
4. `dev/stg/prod`면 `src/plan_and_then_execute_agent/resources/<env>/.env` 추가 로드

## 2. 런타임 핵심 변수

| 변수 | 코드 기본값 | `.env.sample` 예시 | 주요 사용 위치 |
| --- | --- | --- | --- |
| `ENV` | `local`(빈값일 때) | 빈값 | `shared/config/runtime_env_loader.py` |
| `LOG_STDOUT` | `False` | `1` | `shared/logging/logger.py`, `shared/logging/_in_memory_logger.py` |
| `GEMINI_MODEL` | 없음(빈 문자열) | `gemini-3.1-flash-lite-preview` | `core/chat/nodes/*.py` |
| `GEMINI_PROJECT` | 없음(빈 문자열) | 빈값 | `core/chat/nodes/*.py` |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | 동일 | `core/chat/const/settings.py`, `history_repository.py` |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | `200` | `shared/chat/services/chat_service.py` |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | `180` | `api/chat/services/runtime.py` |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | `2` | `api/chat/services/runtime.py` |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | `0.5` | `api/chat/services/runtime.py` |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | 미선언 | `api/chat/services/runtime.py` |
| `CHAT_QUEUE_MAX_SIZE` | `0` | 미선언 | `api/chat/services/runtime.py` (호환 fallback) |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | 미선언 | `api/chat/services/runtime.py` |
| `CHAT_QUEUE_POLL_TIMEOUT` | `0.2` | 미선언 | `api/chat/services/runtime.py` (호환 fallback) |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | 미선언 | `api/chat/services/runtime.py` |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | `0.2` | `api/chat/services/runtime.py` |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | `600` | `api/chat/services/runtime.py` |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | `30` | `api/chat/services/runtime.py` |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | 미선언 | `api/chat/services/runtime.py` |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | `5000` | `integrations/db/engines/sqlite/connection.py` |

## 3. 벡터/엔진 확장 관련 변수

현재 기본 Chat 런타임은 아래 키를 직접 사용하지 않습니다.
아래 값은 엔진 실험, 테스트, 커스텀 조립 시에 사용합니다.

| 변수 | 코드 기본값 | `.env.sample` 예시 | 사용 위치 |
| --- | --- | --- | --- |
| `GEMINI_EMBEDDING_MODEL` | 없음(빈 문자열) | `gemini-embedding-001` | `integrations/embedding/*` 호출부 |
| `GEMINI_EMBEDDING_DIM` | `1024` | `1024` | `shared/config/runtime_env_loader.py` |
| `LANCEDB_URI` | `data/db/vector` | `data/db/vector` | `integrations/db/engines/lancedb/*` |
| `ELASTICSEARCH_SCHEME` | 엔진 기본값 참조 | `https` | `integrations/db/engines/elasticsearch/*` |
| `ELASTICSEARCH_HOST` | 엔진 기본값 참조 | `127.0.0.1` | `integrations/db/engines/elasticsearch/*` |
| `ELASTICSEARCH_PORT` | 엔진 기본값 참조 | `9200` | `integrations/db/engines/elasticsearch/*` |
| `ELASTICSEARCH_VERIFY_CERTS` | 엔진 기본값 참조 | `true` | `integrations/db/engines/elasticsearch/*` |

## 4. PostgreSQL/MongoDB/Redis 선택 변수

| 변수 | `.env.sample` 예시 | 사용 맥락 |
| --- | --- | --- |
| `POSTGRES_*` | `127.0.0.1`, `5432`, `postgres` 등 | PostgreSQL 엔진 주입/테스트 |
| `POSTGRES_DSN` | 주석 처리 | DSN 직접 주입 |
| `MONGODB_*` | `127.0.0.1`, `27017` 등 | MongoDB 엔진 주입/테스트 |
| `MONGODB_URI` | 주석 처리 | URI 직접 주입 |
| `REDIS_*` | `127.0.0.1`, `6379` 등 | Redis 엔진 주입/테스트 |
| `REDIS_URL` | 주석 처리 | URL 직접 주입 |

## 5. `.env.sample`에는 있지만 현재 런타임 미반영인 키

아래 키는 현재 `api/chat/services/runtime.py`가 직접 소비하지 않습니다.

1. `CHAT_TASK_MAX_WORKERS`
2. `CHAT_TASK_QUEUE_MAX_SIZE`
3. `CHAT_BUFFER_BACKEND`
4. `CHAT_TASK_STREAM_MAX_CHUNKS`
5. `CHAT_TASK_RESULT_TTL_SECONDS`
6. `CHAT_TASK_MAX_STORED`
7. `CHAT_TASK_CLEANUP_INTERVAL_SECONDS`

## 6. 권장 `.env` 예시 (로컬)

```env
ENV=local
LOG_STDOUT=1

GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=my-gcp-project

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
```

## 7. 장애 징후 빠른 매핑

| 증상 | 우선 점검 변수 | 확인 포인트 |
| --- | --- | --- |
| 채팅 응답 실패 | `GEMINI_MODEL`, `GEMINI_PROJECT` | 값 누락/오타 여부 |
| 스트림 timeout 빈발 | `CHAT_STREAM_TIMEOUT_SECONDS` | 값이 과도하게 작은지 확인 |
| SQLite 잠금 오류 | `CHAT_DB_PATH`, `SQLITE_BUSY_TIMEOUT_MS` | 경로 충돌/timeout 과소 여부 |
| Elasticsearch TLS 검증 실패 | `ELASTICSEARCH_SCHEME`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_VERIFY_CERTS` | HTTPS 사용 시 인증서 경로/검증 설정 확인 |

## 8. 관련 문서

- `docs/setup/overview.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/shared/config.md`
