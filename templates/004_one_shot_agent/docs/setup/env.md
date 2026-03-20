# 환경 변수 상세 설명

루트 `.env.sample`과 현재 코드 소비 지점을 기준으로 정리한 환경 변수 안내서다.

## 1. 로딩 순서

`RuntimeEnvironmentLoader` 기준:

1. 프로젝트 루트 `.env` 로드
2. `ENV` / `APP_ENV` / `APP_STAGE`로 런타임 환경 결정
3. 값이 비어 있으면 `local`
4. `dev/stg/prod`면 `src/one_shot_agent/resources/<env>/.env` 추가 로드

## 2. 기본 런타임 키

기본 `/agent` 실행 경로가 직접 소비하는 키만 정리한다.

| 변수 | 기본값 | 사용 위치 | 설명 |
| --- | --- | --- | --- |
| `ENV` | `local` | `shared/config/runtime_env_loader.py` | 실행 환경 선택 |
| `LOG_STDOUT` | `False` | `shared/logging/_in_memory_logger.py` | stdout 로그 출력 여부 |
| `GEMINI_MODEL` | 빈 문자열 | `core/agent/nodes/*.py` | Gemini 모델명 |
| `GEMINI_PROJECT` | 빈 문자열 | `core/agent/nodes/*.py` | Gemini 프로젝트 식별자 |
| `GEMINI_API_KEY` | 직접 소비 없음 | 외부 Gemini SDK/실행 환경 | Gemini 인증용 키 |
| `AGENT_REQUEST_TIMEOUT_SECONDS` | `180.0` | `api/agent/services/runtime.py` | 1회성 Agent 요청 timeout |

권장 최소 예시:

```env
ENV=local
LOG_STDOUT=1

GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=my-gcp-project
GEMINI_API_KEY=

AGENT_REQUEST_TIMEOUT_SECONDS=180
```

## 3. 선택적 통합/테스트 키

아래 키는 기본 `/agent` 런타임이 자동으로 사용하지 않는다.
`integrations` 레이어의 엔진 테스트나 수동 검증에서만 의미가 있다.

| 변수 | 사용 맥락 |
| --- | --- |
| `POSTGRES_*`, `POSTGRES_DSN` | PostgreSQL CRUD/벡터 테스트와 수동 엔진 검증 |
| `POSTGRES_ENABLE_VECTOR` | PostgreSQL Vector 테스트 활성화 |
| `MONGODB_*`, `MONGODB_URI` | MongoDB CRUD 테스트와 수동 엔진 검증 |
| `REDIS_*`, `REDIS_URL` | Redis CRUD/벡터 테스트와 수동 엔진 검증 |
| `ELASTICSEARCH_*`, `ELASTICSEARCH_HOSTS` | Elasticsearch CRUD/벡터 테스트와 수동 엔진 검증 |
| `SQLITE_BUSY_TIMEOUT_MS` | SQLite 엔진 연결 옵션 |

주의:

1. 위 키들은 `api/agent/services/runtime.py`가 직접 읽지 않는다.
2. 엔진 테스트는 `tests/integrations/db/*`에서 별도로 사용한다.
3. 기본 런타임 설명과 optional integrations 설명을 혼동하지 않는 것이 핵심이다.
4. `shared/runtime` 보존 유틸은 환경 변수 없이 직접 조립해 사용하는 범용 코드이며, 기본 `/agent` 런타임 설정 표면에는 포함되지 않는다.

## 4. 제거된 런타임 키

아래 키는 현재 단일 요청 Agent 런타임에서 제거되었다.

1. 모든 `CHAT_*`
2. `GEMINI_EMBEDDING_MODEL`
3. `GEMINI_EMBEDDING_DIM`
4. `LANCEDB_URI`
5. `SQLITE_DB_DIR`
6. `SQLITE_DB_PATH`

설명:

1. `CHAT_*`는 과거 세션/SSE/작업 큐 경로 잔재였다.
2. `GEMINI_EMBEDDING_*`는 기본 런타임이 직접 사용하지 않는다.
3. `LANCEDB_URI`는 코드가 자동 소비하지 않으므로 root `.env.sample`에서 제외했다.

## 5. 장애 징후 빠른 매핑

| 증상 | 우선 점검 변수 | 확인 포인트 |
| --- | --- | --- |
| Agent 응답 timeout | `AGENT_REQUEST_TIMEOUT_SECONDS` | 값이 과도하게 작은지 확인 |
| Gemini 호출 실패 | `GEMINI_MODEL`, `GEMINI_PROJECT`, `GEMINI_API_KEY` | 누락/오타 여부 확인 |
| SQLite 잠금 오류 | `SQLITE_BUSY_TIMEOUT_MS` | optional SQLite 엔진 테스트 시 timeout 과소 여부 확인 |

## 6. 관련 문서

- `docs/setup/overview.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/shared/config.md`
