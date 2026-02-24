# 환경 변수 상세 가이드

이 문서는 `.env.sample`에 선언된 키와, 코드에서 실제로 읽는 키를 모두 정리한 환경 변수 사전이다.
값의 반영 위치, 기본값, 형식, 장애 징후까지 한 번에 확인할 수 있도록 구성했다.

## 1. 로딩 순서와 우선순위

런타임에서 환경 변수는 아래 순서로 적용된다.

1. `src/rag_chatbot/api/main.py`에서 `RuntimeEnvironmentLoader().load()` 호출
2. 프로젝트 루트 `.env` 로드
3. `ENV`/`APP_ENV`/`APP_STAGE`로 런타임 환경 결정
4. `ENV`가 `dev/stg/prod`이면 `src/rag_chatbot/resources/<env>/.env` 추가 로드
5. 이후 라우터/서비스 import 시점에 `os.getenv(...)` 값이 고정 반영

중요 동작:

1. 환경 변수를 바꿨는데 서버를 재시작하지 않으면 모듈 초기화 값이 갱신되지 않는다.
2. 숫자/불린은 코드에서 `int()/float()` 혹은 직접 파싱한다.
3. 잘못된 숫자 문자열은 런타임 예외를 발생시킬 수 있다.

## 2. 작성 규칙

1. 키/값 사이 공백 없이 `KEY=value` 형태로 작성한다.
2. 경로 값은 상대경로/절대경로 모두 가능하지만, 운영에서는 절대경로를 권장한다.
3. 비밀키(`OPENAI_API_KEY`, `POSTGRES_PW` 등)는 저장소에 커밋하지 않는다.
4. `.env` 변경 후에는 서버 프로세스를 재시작한다.

## 3. 런타임 핵심 변수 (실제 서비스 반영)

| 변수 | 기본값 | 반영 위치 | 형식/허용값 | 영향 |
| --- | --- | --- | --- | --- |
| `ENV` | 비어 있으면 `local` | `shared/config/runtime_env_loader.py` | `local/dev/stg/prod` | 환경별 리소스 `.env` 로딩 경로 결정 |
| `APP_ENV` | 없음 | `shared/config/runtime_env_loader.py` | `development/staging/production` 또는 위 환경값 | `ENV` 대체 후보 키 |
| `APP_STAGE` | 없음 | `shared/config/runtime_env_loader.py` | `local/dev/stg/prod` | `ENV` 대체 후보 키 |
| `LOG_STDOUT` | 코드 기본 `False` (`.env.sample`은 `1`) | `shared/logging/logger.py` | `1/true/yes/on` 또는 그 외 | stdout JSON 로그 출력 여부 |
| `OPENAI_API_KEY` | 없음 | `core/chat/nodes/response_node.py`, `core/chat/nodes/safeguard_node.py` | OpenAI API Key 문자열 | 누락 시 LLM 호출 실패 |
| `OPENAI_MODEL` | 없음 | `core/chat/nodes/response_node.py`, `core/chat/nodes/safeguard_node.py` | 모델명 문자열 | 잘못된 모델명은 호출 오류 원인 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | `core/chat/const/settings.py`, `shared/chat/repositories/history_repository.py` | 파일 경로 | Chat 세션/메시지 영속 파일 위치 |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | `shared/chat/services/chat_service.py` | `1` 이상 정수 | 컨텍스트 메모리 보관량 결정 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | `api/chat/services/runtime.py` | `0` 이상 실수 | 스트림 실행 타임아웃 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | `api/chat/services/runtime.py` | `0` 이상 정수 | 완료 후 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | `api/chat/services/runtime.py` | `0` 이상 실수 | 저장 재시도 간격(초) |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | `0` 이상 정수 | 작업 큐 크기 제한 (`0`은 무제한) |
| `CHAT_QUEUE_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | `0` 이상 정수 | `CHAT_JOB_QUEUE_MAX_SIZE` 미설정 시 호환 fallback |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | `0` 이상 실수 | 워커 queue pop 대기 시간 |
| `CHAT_QUEUE_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | `0` 이상 실수 | `CHAT_JOB_QUEUE_POLL_TIMEOUT` 미설정 시 호환 fallback |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | `api/chat/services/runtime.py` | `0` 이상 정수 | 요청별 이벤트 버퍼 최대 크기 |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | `api/chat/services/runtime.py` | `0` 이상 실수 | SSE 이벤트 pop 대기 시간 |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | `api/chat/services/runtime.py`, `shared/runtime/buffer/model.py` | `1` 이상 정수(권장) | 요청 이벤트 버킷 TTL |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | `api/chat/services/runtime.py`, `shared/runtime/buffer/model.py` | `0` 초과 실수 | 인메모리 버킷 GC 주기 |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | `api/chat/services/runtime.py` | 문자열 | Redis 버퍼 전환 시 키 prefix |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | `integrations/db/engines/sqlite/connection.py` | `0` 이상 정수 | SQLite 잠금 대기 시간 |

## 4. 인프라 연동 변수 (선택 반영)

아래 키는 기본 런타임에서 자동 사용하지 않거나, 주석 예시/테스트에서 사용한다.

| 변수 | 기본값(.env.sample) | 사용 위치 | 상태 | 설명 |
| --- | --- | --- | --- | --- |
| `POSTGRES_DSN` | 없음(주석) | `api/chat/services/runtime.py` 주석, `tests/conftest.py` | 선택 | DSN 직접 주입 (`postgresql://...`) |
| `POSTGRES_HOST` | `127.0.0.1` | `runtime.py` 주석, 테스트 | 선택 | PostgreSQL 호스트 |
| `POSTGRES_PORT` | `5432` | `runtime.py` 주석, 테스트 | 선택 | PostgreSQL 포트 |
| `POSTGRES_USER` | `postgres` | `runtime.py` 주석, 테스트 | 선택 | PostgreSQL 사용자 |
| `POSTGRES_PW` | `postgres` | `runtime.py` 주석, 테스트 | 선택 | PostgreSQL 비밀번호 |
| `POSTGRES_DATABASE` | `playground` | `runtime.py` 주석, 테스트 | 선택 | PostgreSQL DB 이름 |
| `POSTGRES_ENABLE_VECTOR` | `0` | `tests/integrations/db/Vector/test_postgres_engine_vector.py` | 테스트 | pgvector 벡터 테스트 실행 플래그 |
| `MONGODB_URI` | 없음(주석) | `tests/conftest.py`, CRUD 테스트 | 선택 | MongoDB 접속 URI |
| `MONGODB_HOST` | `127.0.0.1` | 테스트, Mongo 엔진 조립 시 사용 | 선택 | MongoDB 호스트 |
| `MONGODB_PORT` | `27017` | 테스트, Mongo 엔진 조립 시 사용 | 선택 | MongoDB 포트 |
| `MONGODB_USER` | 빈값 | 테스트, Mongo 엔진 조립 시 사용 | 선택 | MongoDB 사용자 |
| `MONGODB_PW` | 빈값 | 테스트, Mongo 엔진 조립 시 사용 | 선택 | MongoDB 비밀번호 |
| `MONGODB_DB` | `playground` | 테스트, Mongo 엔진 조립 시 사용 | 선택 | MongoDB 데이터베이스 |
| `MONGODB_AUTH_DB` | 빈값 | 테스트, Mongo 엔진 조립 시 사용 | 선택 | MongoDB 인증 DB |
| `REDIS_URL` | 없음(주석) | `runtime.py` 주석, 테스트 | 선택 | Redis 연결 URL |
| `REDIS_HOST` | `127.0.0.1` | 테스트 | 선택 | Redis 호스트 |
| `REDIS_PORT` | `6379` | 테스트 | 선택 | Redis 포트 |
| `REDIS_DB` | `0` | 테스트 | 선택 | Redis DB 인덱스 |
| `REDIS_PW` | 빈값 | 테스트 | 선택 | Redis 비밀번호 |
| `ELASTICSEARCH_HOSTS` | 없음(주석) | 테스트 | 선택 | Elasticsearch hosts 문자열 |
| `ELASTICSEARCH_SCHEME` | `https` | 테스트 | 선택 | 프로토콜(`http`/`https`) |
| `ELASTICSEARCH_HOST` | `127.0.0.1` | 테스트 | 선택 | Elasticsearch 호스트 |
| `ELASTICSEARCH_PORT` | `9200` | 테스트 | 선택 | Elasticsearch 포트 |
| `ELASTICSEARCH_USER` | 빈값 | 테스트 | 선택 | Elasticsearch 사용자 |
| `ELASTICSEARCH_PW` | 빈값 | 테스트 | 선택 | Elasticsearch 비밀번호 |
| `ELASTICSEARCH_CA_CERTS` | 빈값 | 테스트 | 선택 | CA 인증서 경로(HTTPS + self-signed 환경이면 필수. 절대경로 권장) |
| `ELASTICSEARCH_VERIFY_CERTS` | `true` | 테스트 | 선택 | 인증서 검증 여부 |
| `ELASTICSEARCH_SSL_FINGERPRINT` | 빈값 | 테스트 | 선택 | TLS 지문 검증 값 |
| `LANCEDB_URI` | `data/db/vector` | `core/chat/nodes/rag_retrieve_node.py`, `ingestion/core/db.py` | 선택 | 파일 기반 벡터 저장소 경로 |
| `SQLITE_DB_DIR` | `data/db` | 현재 서비스 코드 직접 미사용 | 선택 | 범용 SQLite 저장 디렉터리 정책용 |
| `SQLITE_DB_PATH` | `data/db/playground.sqlite` | 현재 서비스 코드 직접 미사용 | 선택 | 범용 SQLite DB 경로 정책용 |

## 5. LLM/호환 변수

| 변수 | 기본값(.env.sample) | 사용 위치 | 상태 | 설명 |
| --- | --- | --- | --- | --- |
| `GEMINI_API_KEY` | 빈값 | LLM 테스트 코드 | 선택 | Gemini API 키 |
| `GOOGLE_API_KEY` | 없음 | LLM 테스트 코드 | 선택 | Gemini 키 대체 입력 |
| `CHAT_LLM_PROVIDER` | `gemini` | 테스트/확장 코드 | 선택 | 공급자 라우팅 실험용 키 |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | `.env.sample`, 테스트 코드 | 선택 | Gemini 모델명 |

## 6. `.env.sample`에 있지만 현재 런타임 미반영인 키

아래 키는 현재 `src/rag_chatbot/api/chat/services/runtime.py` 경로에서 직접 읽지 않는다.
필요하면 코드 반영 지점을 함께 추가해야 한다.

| 변수 | 현재 상태 | 메모 |
| --- | --- | --- |
| `CHAT_TASK_MAX_WORKERS` | 미반영 | 워커 개수 고정 조립 구조와 불일치 |
| `CHAT_TASK_QUEUE_MAX_SIZE` | 미반영 | 현재 키는 `CHAT_JOB_QUEUE_MAX_SIZE` |
| `CHAT_BUFFER_BACKEND` | 미반영 | 현재 버퍼는 `InMemoryEventBuffer` 고정 |
| `CHAT_TASK_STREAM_MAX_CHUNKS` | 미반영 | 스트림 청크 제한 키 미사용 |
| `CHAT_TASK_RESULT_TTL_SECONDS` | 미반영 | task 결과 저장소 구조 미사용 |
| `CHAT_TASK_MAX_STORED` | 미반영 | task 상태 저장소 구조 미사용 |
| `CHAT_TASK_CLEANUP_INTERVAL_SECONDS` | 미반영 | task cleanup 스케줄러 미사용 |

## 7. 권장 `.env` 예시

### 7-1. 로컬 기본 실행

```env
ENV=local
LOG_STDOUT=1
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
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

### 7-2. PostgreSQL 전환 준비 예시

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
POSTGRES_DATABASE=playground
# 선택: 하나로 합쳐서 사용
# POSTGRES_DSN=postgresql://postgres:postgres@127.0.0.1:5432/playground
```

### 7-3. MongoDB 전환 준비 예시

```env
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
MONGODB_USER=
MONGODB_PW=
MONGODB_DB=playground
MONGODB_AUTH_DB=
# 선택: URI 직접 사용
# MONGODB_URI=mongodb://127.0.0.1:27017
```

### 7-4. Elasticsearch TLS(자체 서명 인증서) 예시

```env
ELASTICSEARCH_SCHEME=https
ELASTICSEARCH_HOST=127.0.0.1
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PW=your-password
ELASTICSEARCH_VERIFY_CERTS=true
# 상대경로 예시
# ELASTICSEARCH_CA_CERTS=certs/http_ca.crt
# 절대경로 예시(권장)
ELASTICSEARCH_CA_CERTS=/home/kkh93/proj/TemplateZoo/templates/000_rag_chatbot/certs/http_ca.crt
```

권장 점검 순서:

1. `ELASTICSEARCH_VERIFY_CERTS=true`이면 `ELASTICSEARCH_CA_CERTS`를 반드시 설정한다.
2. `curl --cacert "$ELASTICSEARCH_CA_CERTS" -u elastic:$ELASTICSEARCH_PW https://127.0.0.1:9200`로 인증서 신뢰 여부를 먼저 확인한다.
3. 테스트 실행 전에 `ELASTICSEARCH_CA_CERTS`가 빈값이 아닌지 재확인한다.

## 8. 장애 징후 빠른 매핑

| 증상 | 우선 점검 변수 | 확인 포인트 |
| --- | --- | --- |
| 서버는 뜨지만 채팅 응답이 계속 실패 | `OPENAI_API_KEY`, `OPENAI_MODEL` | 키 누락/모델명 오타 |
| 요청이 오래 걸리다 timeout | `CHAT_STREAM_TIMEOUT_SECONDS` | 너무 작은 값 설정 여부 |
| 메모리 사용량 증가 | `CHAT_MEMORY_MAX_MESSAGES`, `CHAT_EVENT_BUFFER_TTL_SECONDS` | 보관량/TTL 과다 여부 |
| SQLite 잠금 오류 빈발 | `CHAT_DB_PATH`, `SQLITE_BUSY_TIMEOUT_MS` | 파일 경로 충돌, timeout 과소 |
| 로그가 stdout에 안 보임 | `LOG_STDOUT` | `1/true/yes/on` 값 여부 |
| pgvector 테스트가 항상 skip | `POSTGRES_ENABLE_VECTOR` | 값이 `1`인지 확인 |
| Elasticsearch TLS 검증 실패(`CERTIFICATE_VERIFY_FAILED`) | `ELASTICSEARCH_SCHEME`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_VERIFY_CERTS` | `https` 사용 시 CA 경로 누락/오경로 여부 확인 |

## 9. 관련 문서

- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/setup/filesystem.md`
- `docs/shared/config.md`
