# 환경 변수 상세 레퍼런스

이 문서는 `.env.sample` 키와 코드에서 실제 소비하는 키를 정리한 환경 변수 사전이다.
최근 장애 사례(Elasticsearch TLS 권한, Mongo authSource, E2E timeout)를 기준으로 점검 순서를 함께 제공한다.

## 1. 로딩 순서와 우선순위

1. `src/chatbot/api/main.py`에서 `RuntimeEnvironmentLoader().load()` 호출
2. 프로젝트 루트 `.env` 로드
3. `ENV`/`APP_ENV`/`APP_STAGE`로 런타임 환경 결정
4. `ENV`가 `dev/stg/prod`이면 `src/chatbot/resources/<env>/.env` 추가 로드
5. 모듈 import 시점의 `os.getenv(...)` 값이 고정 반영

중요:

1. `.env` 변경 후 프로세스를 재시작하지 않으면 값이 갱신되지 않는다.
2. 숫자/불린 파싱 오류는 런타임 예외를 유발할 수 있다.

## 2. 작성 기준

1. `KEY=value` 형식으로 작성한다.
2. 경로 값은 운영에서 절대경로를 권장한다.
3. 비밀값은 저장소에 커밋하지 않는다.
4. 변경 후 서버/테스트 프로세스를 재시작한다.

## 3. 런타임 핵심 변수

| 변수 | 기본값 | 반영 위치 | 형식/허용값 | 영향 |
| --- | --- | --- | --- | --- |
| `ENV` | 비어 있으면 `local` | `shared/config/runtime_env_loader.py` | `local/dev/stg/prod` | 환경별 리소스 `.env` 로딩 |
| `APP_ENV` | 없음 | `shared/config/runtime_env_loader.py` | `development/staging/production` | `ENV` 대체 후보 |
| `APP_STAGE` | 없음 | `shared/config/runtime_env_loader.py` | `local/dev/stg/prod` | `ENV` 대체 후보 |
| `LOG_STDOUT` | 코드 기본 `False` | `shared/logging/logger.py` | `1/true/yes/on` | stdout 로그 출력 여부 |
| `GEMINI_MODEL` | 없음 | `core/chat/nodes/response_node.py`, `core/chat/nodes/safeguard_node.py`, 테스트 fixture | 모델명 문자열 | 누락/오타 시 LLM 호출 실패 |
| `GEMINI_PROJECT` | 없음 | 동일 | GCP 프로젝트 문자열 | 누락 시 LLM 호출 실패 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | `core/chat/const/settings.py` | 파일 경로 | Chat 저장 파일 위치 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | `shared/chat/services/chat_service.py` | `1` 이상 정수 | 컨텍스트 메모리 보관량 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | `api/chat/services/runtime.py` | `0` 이상 실수 | 스트림 실행 타임아웃 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | `api/chat/services/runtime.py` | `0` 이상 정수 | 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | `api/chat/services/runtime.py` | `0` 이상 실수 | 저장 재시도 간격 |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | `0` 이상 정수 | 작업 큐 크기 제한 |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | `0` 이상 실수 | 큐 poll 대기 시간 |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | `0` 이상 정수 | 이벤트 버퍼 크기 |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | `0` 이상 실수 | 이벤트 poll 대기 시간 |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | `api/chat/services/runtime.py` | `1` 이상 정수 권장 | 이벤트 버킷 TTL |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | `api/chat/services/runtime.py` | `0` 초과 실수 | InMemory GC 주기 |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | `api/chat/services/runtime.py` | 문자열 | Redis 버퍼 키 prefix |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | `integrations/db/engines/sqlite/connection.py` | `0` 이상 정수 | SQLite 잠금 대기 |

## 4. 인프라 연동 변수(테스트/선택)

| 변수 | 기본값(.env.sample) | 사용 위치 | 설명 |
| --- | --- | --- | --- |
| `POSTGRES_DSN` | 없음 | 테스트/선택 조립 | PostgreSQL DSN |
| `POSTGRES_HOST` | `127.0.0.1` | 테스트/선택 조립 | PostgreSQL 호스트 |
| `POSTGRES_PORT` | `5432` | 테스트/선택 조립 | PostgreSQL 포트 |
| `POSTGRES_USER` | `postgres` | 테스트/선택 조립 | PostgreSQL 사용자 |
| `POSTGRES_PW` | `postgres` | 테스트/선택 조립 | PostgreSQL 비밀번호 |
| `POSTGRES_DATABASE` | `playground` | 테스트/선택 조립 | PostgreSQL DB |
| `POSTGRES_ENABLE_VECTOR` | `0` | 벡터 테스트 | PostgreSQL 벡터 테스트 플래그 |
| `MONGODB_URI` | 없음 | 테스트/선택 조립 | Mongo URI |
| `MONGODB_HOST` | `127.0.0.1` | 테스트/선택 조립 | Mongo 호스트 |
| `MONGODB_PORT` | `27017` | 테스트/선택 조립 | Mongo 포트 |
| `MONGODB_USER` | 빈값 | 테스트/선택 조립 | Mongo 사용자 |
| `MONGODB_PW` | 빈값 | 테스트/선택 조립 | Mongo 비밀번호 |
| `MONGODB_DB` | `playground` | 테스트/선택 조립 | 데이터베이스 |
| `MONGODB_AUTH_DB` | 빈값 | 테스트/선택 조립 | 인증 DB(`authSource`) |
| `REDIS_URL` | 없음 | 테스트/선택 조립 | Redis URL |
| `REDIS_HOST` | `127.0.0.1` | 테스트 | Redis 호스트 |
| `REDIS_PORT` | `6379` | 테스트 | Redis 포트 |
| `REDIS_DB` | `0` | 테스트 | Redis DB 인덱스 |
| `REDIS_PW` | 빈값 | 테스트 | Redis 비밀번호 |
| `ELASTICSEARCH_HOSTS` | 없음 | 테스트 | Elasticsearch hosts 문자열 |
| `ELASTICSEARCH_SCHEME` | `https` | 테스트 | `http`/`https` |
| `ELASTICSEARCH_HOST` | `127.0.0.1` | 테스트 | Elasticsearch 호스트 |
| `ELASTICSEARCH_PORT` | `9200` | 테스트 | Elasticsearch 포트 |
| `ELASTICSEARCH_USER` | 빈값 | 테스트 | Elasticsearch 사용자 |
| `ELASTICSEARCH_PW` | 빈값 | 테스트 | Elasticsearch 비밀번호 |
| `ELASTICSEARCH_CA_CERTS` | 빈값 | 테스트 | HTTPS CA 인증서 경로 |
| `ELASTICSEARCH_VERIFY_CERTS` | `true` | 테스트 | 인증서 검증 여부 |
| `ELASTICSEARCH_SSL_FINGERPRINT` | 빈값 | 테스트 | 지문 검증 값 |
| `LANCEDB_URI` | `data/db/vector` | LanceDB 구성 | 벡터 저장 경로 |

## 5. Gemini 정책값과 구현 차이

정책 기준:

1. 문서 표준 설정은 `thinking_level="minimal"`로 정의한다.

구현 전환 중 주석:

1. 현재 일부 코드/fixture는 `thinking_level="low"`를 사용하고 있다.
2. 정책값(`minimal`)으로 수렴 중이며, 문서/코드 동기화 시점에 맞춰 업데이트한다.

## 6. 권장 `.env` 예시

### 6-1. 로컬 기본 실행

```env
ENV=local
LOG_STDOUT=1
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_PROJECT=your-project
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

### 6-2. MongoDB 인증 예시

```env
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
MONGODB_USER=admin
MONGODB_PW=admin
MONGODB_DB=playground
MONGODB_AUTH_DB=admin
```

### 6-3. Elasticsearch TLS 예시

```env
ELASTICSEARCH_SCHEME=https
ELASTICSEARCH_HOST=127.0.0.1
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PW=your-password
ELASTICSEARCH_VERIFY_CERTS=true
ELASTICSEARCH_CA_CERTS=/abs/path/to/certs/http_ca.crt
```

## 7. 장애 징후 빠른 매핑

| 증상 | 우선 점검 변수 | 확인 포인트 |
| --- | --- | --- |
| LLM 호출 실패 | `GEMINI_MODEL`, `GEMINI_PROJECT` | 누락/오타 여부 |
| 서버 기동은 되지만 스트림 timeout | `CHAT_STREAM_TIMEOUT_SECONDS` | 값이 너무 작은지 확인 |
| Mongo 인증 실패(`Authentication failed`) | `MONGODB_USER`, `MONGODB_PW`, `MONGODB_DB`, `MONGODB_AUTH_DB` | 인증 DB와 사용자 생성 DB 일치 여부 |
| Elasticsearch TLS 실패(`CERTIFICATE_VERIFY_FAILED`) | `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_VERIFY_CERTS` | CA 경로/유효성 |
| Elasticsearch TLS 실패(`Permission denied`) | `ELASTICSEARCH_CA_CERTS` 파일 권한 | 실행 사용자 읽기 권한 |
| SSE `done` 미수신 | `CHAT_STREAM_TIMEOUT_SECONDS` + 클라이언트 read timeout | `error` 종료 여부 함께 확인 |

## 8. 즉시 점검 명령

```bash
printf 'GEMINI_MODEL=%s\nGEMINI_PROJECT=%s\n' "$GEMINI_MODEL" "$GEMINI_PROJECT"
printf 'MONGODB_DB=%s\nMONGODB_AUTH_DB=%s\n' "$MONGODB_DB" "$MONGODB_AUTH_DB"
ls -l "$ELASTICSEARCH_CA_CERTS"
head -n 1 "$ELASTICSEARCH_CA_CERTS"
```

기대 결과:

1. Gemini 필수 값이 비어 있지 않다.
2. Mongo 인증 DB가 의도와 일치한다.
3. Elasticsearch CA 파일을 현재 사용자로 읽을 수 있다.

## 9. 관련 문서

- `docs/setup/troubleshooting.md`
- `docs/setup/sqlite.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/integrations/db.md`
