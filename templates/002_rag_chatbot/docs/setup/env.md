# 환경 변수 상세 가이드

이 문서는 `.env.sample` 선언값과 코드(`os.getenv`) 소비 지점을 함께 정리한 환경 변수 사전이다.

## 1. 로딩 순서

런타임 로더(`RuntimeEnvironmentLoader`) 기준:

1. 프로젝트 루트 `.env` 로드
2. `ENV`/`APP_ENV`/`APP_STAGE`로 런타임 환경 결정
3. 값이 비어 있으면 `local`
4. `dev/stg/prod`면 `src/rag_chatbot/resources/<env>/.env` 추가 로드

주의:

1. 서버 재시작 전에는 모듈 초기화 값이 갱신되지 않는다.
2. 숫자/불린 파싱 실패는 런타임 예외로 이어질 수 있다.

## 2. 기본값 해석 규칙

문서의 기본값 표기는 두 가지를 구분한다.

1. 코드 기본값: `os.getenv("KEY", "...")`의 fallback 값
2. 샘플 기본값: `.env.sample`에 적힌 예시값

같은 키라도 코드 기본값과 샘플 예시값이 다를 수 있다.

## 3. 런타임 핵심 변수

| 변수 | 코드 기본값 | `.env.sample` 예시 | 주요 사용 위치 |
| --- | --- | --- | --- |
| `ENV` | `local`(빈값일 때) | 빈값 | `shared/config/runtime_env_loader.py` |
| `LOG_STDOUT` | `False` | `1` | `shared/logging/logger.py` |
| `GEMINI_MODEL` | 없음(빈 문자열) | `gemini-3.1-flash-lite-preview` | `core/chat/nodes/*.py`, `ingestion/core/runner.py` |
| `GEMINI_PROJECT` | 없음(빈 문자열) | 빈값 | `core/chat/nodes/*.py`, `ingestion/core/runner.py` |
| `GEMINI_EMBEDDING_MODEL` | 없음(빈 문자열) | `gemini-embedding-001` | `core/chat/nodes/rag_retrieve_node.py`, `ingestion/core/runner.py` |
| `GEMINI_EMBEDDING_DIM` | `1024` | `1024` | `shared/config/runtime_env_loader.py`, `rag_retrieve_node.py`, `ingestion/core/runner.py` |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | `data/db/chat/chat_history.sqlite` | `core/chat/const/settings.py`, `history_repository.py` |
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

## 4. ingestion/벡터 저장소 관련 변수

| 변수 | 코드 기본값 | `.env.sample` 예시 | 사용 위치 |
| --- | --- | --- | --- |
| `LANCEDB_URI` | `data/db/vector` | `data/db/vector` | `rag_retrieve_node.py`, `ingestion/core/db.py` |
| `ELASTICSEARCH_SCHEME` | `http`(ingestion 코드) | `https` | `ingestion/core/db.py` |
| `ELASTICSEARCH_HOST` | `127.0.0.1` | `127.0.0.1` | `ingestion/core/db.py` |
| `ELASTICSEARCH_PORT` | `9200` | `9200` | `ingestion/core/db.py` |
| `ELASTICSEARCH_VERIFY_CERTS` | `true` | `true` | `ingestion/core/db.py` |

주의:

1. `ELASTICSEARCH_SCHEME`는 ingestion 코드 기본이 `http`지만, 샘플은 `https` 예시다.
2. HTTPS를 쓸 때는 `ELASTICSEARCH_CA_CERTS`와 인증 정책을 함께 설정해야 한다.

## 5. PostgreSQL/MongoDB/Redis 선택 변수

| 변수 | `.env.sample` 예시 | 사용 맥락 |
| --- | --- | --- |
| `POSTGRES_*` | `127.0.0.1`, `5432`, `postgres` 등 | PostgreSQL 엔진 주입/테스트 |
| `POSTGRES_DSN` | 주석 처리 | DSN 직접 주입 |
| `MONGODB_*` | `127.0.0.1`, `27017` 등 | MongoDB 엔진 주입/테스트 |
| `MONGODB_URI` | 주석 처리 | URI 직접 주입 |
| `REDIS_*` | `127.0.0.1`, `6379` 등 | Redis 엔진 주입/테스트 |
| `REDIS_URL` | 주석 처리 | URL 직접 주입 |

## 6. `.env.sample`에는 있지만 현재 런타임 미반영인 키

아래 키는 현재 `api/chat/services/runtime.py`가 직접 소비하지 않는다.

1. `CHAT_TASK_MAX_WORKERS`
2. `CHAT_TASK_QUEUE_MAX_SIZE`
3. `CHAT_BUFFER_BACKEND`
4. `CHAT_TASK_STREAM_MAX_CHUNKS`
5. `CHAT_TASK_RESULT_TTL_SECONDS`
6. `CHAT_TASK_MAX_STORED`
7. `CHAT_TASK_CLEANUP_INTERVAL_SECONDS`

## 7. 권장 `.env` 예시 (로컬)

```env
ENV=local
LOG_STDOUT=1

GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_PROJECT=my-gcp-project
GEMINI_EMBEDDING_DIM=1024

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

LANCEDB_URI=data/db/vector
```

## 8. 장애 징후 빠른 매핑

| 증상 | 우선 점검 변수 | 확인 포인트 |
| --- | --- | --- |
| 채팅 응답 실패 | `GEMINI_MODEL`, `GEMINI_PROJECT` | 값 누락/오타 여부 |
| ingestion 후 검색 실패 | `GEMINI_EMBEDDING_DIM` | 저장소 기존 차원과 설정 차원 일치 여부 |
| 스트림 timeout 빈발 | `CHAT_STREAM_TIMEOUT_SECONDS` | 값이 과도하게 작은지 확인 |
| SQLite 잠금 오류 | `CHAT_DB_PATH`, `SQLITE_BUSY_TIMEOUT_MS` | 경로 충돌/timeout 과소 여부 |
| Elasticsearch TLS 검증 실패 | `ELASTICSEARCH_SCHEME`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_VERIFY_CERTS` | HTTPS 사용 시 인증서 경로/검증 설정 확인 |

## 9. 관련 문서

- `docs/setup/overview.md`
- `docs/setup/ingestion.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/shared/config.md`
