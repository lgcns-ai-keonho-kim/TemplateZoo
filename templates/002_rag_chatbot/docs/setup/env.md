# 환경 변수 상세 가이드

이 문서는 `.env.sample`과 실제 코드 소비 지점을 기준으로 현재 환경 변수를 정리한다.

## 1. 로딩 순서

1. 프로젝트 루트 `.env`
2. `ENV`, `APP_ENV`, `APP_STAGE` 해석
3. 빈값이면 `local`
4. `dev/stg/prod`면 `src/rag_chatbot/resources/<env>/.env`

## 2. 핵심 변수

| 변수 | 코드 기본값 | 주요 사용 위치 |
| --- | --- | --- |
| `ENV` | `local` | `shared/config/runtime_env_loader.py` |
| `LOG_STDOUT` | `False` | `shared/logging/logger.py` |
| `GEMINI_MODEL` | 빈 문자열 | core 노드, ingestion 주석 생성 |
| `GEMINI_PROJECT` | 빈 문자열 | core 노드, ingestion |
| `GEMINI_EMBEDDING_MODEL` | 빈 문자열 | `rag_retrieve_node.py`, ingestion |
| `GEMINI_EMBEDDING_DIM` | `1024` | retrieval, ingestion |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | core const, repository |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | SQLite connection |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | `ChatService` |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | `runtime.py` |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | `runtime.py` |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | `runtime.py` |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | `runtime.py` |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | `runtime.py` |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | `runtime.py` |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | `runtime.py` |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | `runtime.py` |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | `runtime.py` |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | `runtime.py` |
| `LANCEDB_URI` | `data/db/vector` | retrieval, ingestion |

## 3. 현재 직접 소비하지 않는 샘플 키

- `CHAT_TASK_MAX_WORKERS`
- `CHAT_TASK_QUEUE_MAX_SIZE`
- `CHAT_BUFFER_BACKEND`
- `CHAT_TASK_STREAM_MAX_CHUNKS`
- `CHAT_TASK_RESULT_TTL_SECONDS`
- `CHAT_TASK_MAX_STORED`
- `CHAT_TASK_CLEANUP_INTERVAL_SECONDS`

## 4. 유지보수/추가개발 포인트

- `.env.sample`에 키가 있다고 해서 현재 runtime이 직접 소비하는 것은 아니다. 반드시 실제 `os.getenv()` 지점을 같이 확인해야 한다.
- 차원, backend, queue 관련 키를 바꾸면 재적재나 재시작이 필요한지 문서에 분명히 적는 편이 좋다.
- 환경 변수 이름을 바꾸면 README, setup 문서, 배포 스크립트까지 함께 수정해야 한다.

## 5. 관련 문서

- `docs/shared/config.md`
- `docs/setup/ingestion.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
