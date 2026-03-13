# 환경 변수 상세 설명

현재 기본 런타임(`POST /agent`)이 실제로 사용하는 환경 변수와, 선택적 확장 경로에서만 의미가 있는 변수를 구분해 정리한다.

## 1. 로딩 순서

`RuntimeEnvironmentLoader` 기준:

1. 프로젝트 루트 `.env` 로드
2. `ENV` / `APP_ENV` / `APP_STAGE`로 런타임 환경 결정
3. 값이 비어 있으면 `local`
4. `dev/stg/prod`면 `src/single_request_tool_agent/resources/<env>/.env` 추가 로드

## 2. 기본 런타임 핵심 변수

| 변수 | 코드 기본값 | 주요 사용 위치 |
| --- | --- | --- |
| `ENV` | `local` | `shared/config/runtime_env_loader.py` |
| `LOG_STDOUT` | `False` | `shared/logging/logger.py` |
| `GEMINI_MODEL` | 빈 문자열 | `core/agent/nodes/*.py` |
| `GEMINI_PROJECT` | 빈 문자열 | `core/agent/nodes/*.py` |
| `AGENT_REQUEST_TIMEOUT_SECONDS` | `180` | `api/agent/services/runtime.py` |

권장 로컬 예시:

```env
ENV=local
LOG_STDOUT=1

GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=my-gcp-project
GEMINI_API_KEY=

AGENT_REQUEST_TIMEOUT_SECONDS=180
```

## 3. 현재 기본 런타임에서 사용하지 않는 구 Chat 변수

아래 `CHAT_*` 변수는 과거 세션/SSE/큐 기반 경로의 흔적이며, 현재 기본 `/agent` 런타임에서는 직접 사용하지 않는다.

1. `CHAT_DB_PATH`
2. `CHAT_MEMORY_MAX_MESSAGES`
3. `CHAT_STREAM_TIMEOUT_SECONDS`
4. `CHAT_PERSIST_RETRY_LIMIT`
5. `CHAT_PERSIST_RETRY_DELAY_SECONDS`
6. `CHAT_JOB_QUEUE_MAX_SIZE`
7. `CHAT_JOB_QUEUE_POLL_TIMEOUT`
8. `CHAT_EVENT_BUFFER_MAX_SIZE`
9. `CHAT_EVENT_BUFFER_POLL_TIMEOUT`
10. `CHAT_EVENT_BUFFER_TTL_SECONDS`
11. `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS`
12. `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX`

주의:

1. 이 변수들은 `src`에 남아 있는 보조/레거시 모듈에서만 의미가 있을 수 있다.
2. 현재 공개 API와 기본 실행 경로는 위 변수 없이 동작한다.

## 4. 선택적 인프라/테스트 변수

아래 변수들은 기본 `/agent` 런타임이 직접 소비하지 않지만, 엔진 테스트나 수동 조립 코드에서 의미가 있다.

| 범주 | 예시 변수 | 사용 맥락 |
| --- | --- | --- |
| PostgreSQL | `POSTGRES_*`, `POSTGRES_DSN` | DB 엔진 테스트, 수동 조립 |
| MongoDB | `MONGODB_*`, `MONGODB_URI` | DB 엔진 테스트, 수동 조립 |
| Redis | `REDIS_*`, `REDIS_URL` | Redis 엔진 테스트 |
| Elasticsearch | `ELASTICSEARCH_*` | Elasticsearch 엔진 테스트 |
| Embedding | `GEMINI_EMBEDDING_*` | 임베딩/검증 헬퍼 |

## 5. 장애 징후 빠른 매핑

| 증상 | 우선 점검 변수 | 확인 포인트 |
| --- | --- | --- |
| `/agent` 응답 실패 | `GEMINI_MODEL`, `GEMINI_PROJECT` | 값 누락/오타 여부 |
| 요청 시간 초과 | `AGENT_REQUEST_TIMEOUT_SECONDS` | 값이 과도하게 작은지 확인 |
| 로그가 stdout에 안 보임 | `LOG_STDOUT` | `1` 또는 적절한 로깅 설정 여부 |

## 6. 관련 문서

- `docs/setup/overview.md`
- `docs/api/agent.md`
- `docs/shared/config.md`
