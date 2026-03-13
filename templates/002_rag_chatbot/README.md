# RAG Chatbot Template

LLM 기반 RAG Chatbot을 빠르게 시작하기 위한 Python/FastAPI 템플릿이다.
권장 Python 버전은 `3.13+`이다.

## 1. 빠른 시작

### 1-1. 프로젝트명 초기화(선택)

```bash
bash init.sh my-project
```

- 단일 인자로 받는다.
- 내부에서 자동 변환:
- `PROJECT_SLUG`: `my-project` 형태
- `PACKAGE_NAME`: `my_project` 형태

### 1-2. 가상환경/의존성 설치

```bash
uv venv .venv
uv sync
```

### 1-3. 환경 변수 파일 생성

기본 로컬 실행:

```bash
cp .env.sample .env
```

현재 기본 채팅 그래프(`src/rag_chatbot/core/chat/nodes/*.py`)와 ingestion 파이프라인(`ingestion/*.py`)은 Gemini 설정을 사용한다.

```env
ENV=local
LOG_STDOUT=1

GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=your-project
GEMINI_API_KEY=

GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIM=1024
LANCEDB_URI=data/db/vector
```

런타임 환경이 `dev/stg/prod`인 경우에는 루트 `.env` 외에 환경별 리소스 파일도 준비해야 한다.

예시(`dev`):

```bash
cp src/rag_chatbot/resources/dev/.env.sample src/rag_chatbot/resources/dev/.env
```

### 1-4. RAG 데이터 적재

기본 벡터 저장소는 LanceDB(`LANCEDB_URI`)다.
입력 문서 기본 경로는 `data/ingestion-doc`이며, 지원 형식은 `.pdf`, `.docx`, `.md`, `.markdown`이다.

```bash
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc
```

선택 가능한 백엔드:

- `lancedb`
- `postgres`
- `elasticsearch`

### 1-5. 서버 실행

```bash
uv run uvicorn rag_chatbot.api.main:app --host 0.0.0.0 --port 8000 --reload
```

`RuntimeEnvironmentLoader`가 아래 순서로 환경을 로드한다.

1. 프로젝트 루트 `.env`
2. `ENV`/`APP_ENV`/`APP_STAGE` 해석
3. 값이 비어 있으면 `local`
4. `ENV=dev/stg/prod`면 `src/rag_chatbot/resources/<env>/.env`

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 정적 UI: `http://127.0.0.1:8000/ui`

## 2. API 인터페이스 요약

### 2-1. Chat API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/chat` | 채팅 작업 제출 (`session_id`, `message`, `context_window`) |
| `GET` | `/chat/{session_id}` | 세션 스냅샷(메시지/최근 상태) 조회 |
| `GET` | `/chat/{session_id}/events?request_id=...` | 요청 단위 SSE 이벤트 구독 |

### 2-2. UI API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/ui-api/chat/sessions` | UI 세션 생성 |
| `GET` | `/ui-api/chat/sessions` | UI 세션 목록 |
| `GET` | `/ui-api/chat/sessions/{session_id}/messages` | UI 메시지 목록 |
| `DELETE` | `/ui-api/chat/sessions/{session_id}` | 세션+메시지 삭제 |

### 2-3. Health API

| Method | Path | 설명 |
| --- | --- | --- |
| `GET` | `/health` | 서버 생존 상태 확인 |

## 3. 동작 방식

현재 시스템은 `세션 + 비동기 실행 + SSE + 다단 RAG` 구조로 동작한다.

1. UI는 `/ui-api/chat/sessions`로 세션 목록을 조회하고 활성 세션을 정한다.
2. 사용자가 메시지를 보내면 `POST /chat`을 호출한다.
3. 서버는 `session_id`, `request_id`, `status=QUEUED`를 즉시 반환한다.
4. UI는 `GET /chat/{session_id}/events?request_id=...`로 요청 단위 스트림을 구독한다.
5. `ServiceExecutor`가 작업 큐를 소비하며 `start -> token* -> references? -> done/error` 이벤트를 전송한다.
6. `ChatService`는 사용자 메시지 저장, 히스토리 로드, 그래프 실행, assistant 응답 영속화를 담당한다.
7. 그래프는 `safeguard -> context_strategy -> RAG -> response` 또는 `blocked` 경로로 분기한다.
8. `rag_format` 단계가 참고 문서를 `rag_references`로 만들고, 상위 계층이 이를 `references` SSE 이벤트로 정규화한다.
9. 완료 시 assistant 응답은 `request_id` 멱등 기준으로 1회만 저장된다.
10. 필요하면 `GET /chat/{session_id}`로 최종 스냅샷을 조회한다.

SSE `data` 예시:

```json
{
  "session_id": "...",
  "request_id": "...",
  "type": "token",
  "node": "response",
  "content": "안녕하세요",
  "status": null,
  "error_message": null,
  "metadata": {}
}
```

이벤트 타입:

- `start`
- `token`
- `references`
- `done`
- `error`

## 4. 환경 변수 (`.env`)

기본 샘플: `.env.sample`

전체 키 상세 설명과 로딩 우선순위는 `docs/setup/env.md`를 참고한다.

### 4-1. 런타임/로그

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ENV` | `local`(빈값일 때) | `local/dev/stg/prod` 런타임 선택 |
| `LOG_STDOUT` | `False` | stdout 로그 출력 여부 |

### 4-2. Chat/RAG 실행 핵심

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `GEMINI_MODEL` | - | safeguard, context strategy, relevance judge, response 등 기본 LLM 모델명 |
| `GEMINI_PROJECT` | - | Google Cloud 프로젝트 식별자 |
| `GEMINI_API_KEY` | - | 필요 시 Gemini 인증에 사용하는 API 키 |
| `GEMINI_EMBEDDING_MODEL` | - | RAG 검색과 ingestion 임베딩 모델명 |
| `GEMINI_EMBEDDING_DIM` | `1024` | 임베딩 벡터 차원 |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | Chat 이력 SQLite 경로 |
| `SQLITE_BUSY_TIMEOUT_MS` | `5000` | SQLite 잠금 대기 시간(ms) |
| `CHAT_MEMORY_MAX_MESSAGES` | `200` | 세션 메모리 최대 메시지 수 |
| `CHAT_STREAM_TIMEOUT_SECONDS` | `180` | SSE 대기/실행 타임아웃 |
| `CHAT_PERSIST_RETRY_LIMIT` | `2` | 완료 저장 재시도 횟수 |
| `CHAT_PERSIST_RETRY_DELAY_SECONDS` | `0.5` | 완료 저장 재시도 간격(초) |
| `CHAT_JOB_QUEUE_MAX_SIZE` | `0` | 작업 큐 최대 크기 (`0` 무제한) |
| `CHAT_QUEUE_MAX_SIZE` | `0` | 기존 키와의 호환용 큐 크기 fallback |
| `CHAT_JOB_QUEUE_POLL_TIMEOUT` | `0.2` | 작업 큐 poll timeout(초) |
| `CHAT_QUEUE_POLL_TIMEOUT` | `0.2` | 기존 키와의 호환용 큐 poll fallback |
| `CHAT_EVENT_BUFFER_MAX_SIZE` | `0` | 이벤트 버퍼 최대 크기 (`0` 무제한) |
| `CHAT_EVENT_BUFFER_POLL_TIMEOUT` | `0.2` | 이벤트 버퍼 pop timeout(초) |
| `CHAT_EVENT_BUFFER_TTL_SECONDS` | `600` | 이벤트 버퍼 TTL(초) |
| `CHAT_EVENT_BUFFER_GC_INTERVAL_SECONDS` | `30` | 인메모리 버퍼 GC 주기(초) |
| `CHAT_REDIS_EVENT_BUFFER_KEY_PREFIX` | `chat:stream` | Redis 이벤트 키 prefix |

### 4-3. ingestion/벡터 저장소

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `LANCEDB_URI` | `data/db/vector` | LanceDB 벡터 저장 경로 |
| `POSTGRES_HOST` | `127.0.0.1` | PostgreSQL 호스트 |
| `POSTGRES_PORT` | `5432` | PostgreSQL 포트 |
| `POSTGRES_USER` | `postgres` | PostgreSQL 사용자 |
| `POSTGRES_PW` | `postgres` | PostgreSQL 비밀번호 |
| `POSTGRES_DATABASE` | `playground` | PostgreSQL 데이터베이스명 |
| `POSTGRES_DSN` | - | PostgreSQL DSN 직접 주입 |
| `MONGODB_HOST` | `127.0.0.1` | MongoDB 호스트 |
| `MONGODB_PORT` | `27017` | MongoDB 포트 |
| `MONGODB_DB` | `playground` | MongoDB 데이터베이스명 |
| `MONGODB_URI` | - | MongoDB URI 직접 주입 |
| `REDIS_HOST` | `127.0.0.1` | Redis 호스트 |
| `REDIS_PORT` | `6379` | Redis 포트 |
| `REDIS_DB` | `0` | Redis DB 인덱스 |
| `REDIS_URL` | - | Redis URL 직접 주입 |
| `ELASTICSEARCH_SCHEME` | `http`(코드 기준) | Elasticsearch 스킴 |
| `ELASTICSEARCH_HOST` | `127.0.0.1` | Elasticsearch 호스트 |
| `ELASTICSEARCH_PORT` | `9200` | Elasticsearch 포트 |
| `ELASTICSEARCH_VERIFY_CERTS` | `true` | TLS 인증서 검증 여부 |
| `ELASTICSEARCH_CA_CERTS` | - | HTTPS용 CA 인증서 경로 |
| `ELASTICSEARCH_SSL_FINGERPRINT` | - | 지문 기반 TLS 검증 값 |

참고:

- `.env.sample`에는 `CHAT_TASK_*`, `CHAT_BUFFER_BACKEND` 같은 키도 남아 있지만, 현재 `src/rag_chatbot/api/chat/services/runtime.py`는 직접 사용하지 않는다.
- `ENV=dev/stg/prod`를 사용할 때는 `src/rag_chatbot/resources/<env>/.env`가 추가로 필요하다.
- 설정 값은 import 시점에 고정 반영되는 모듈이 있으므로 변경 후 프로세스를 재시작해야 한다.

### 4-4. 외부 저장소 전환 메모

1. 현재 기본 Chat 저장소는 SQLite(`CHAT_DB_PATH`)다.
2. 현재 작업 큐와 이벤트 버퍼는 `src/rag_chatbot/api/chat/services/runtime.py` 기준으로 `InMemoryQueue`, `InMemoryEventBuffer`를 고정 사용한다.
3. PostgreSQL/MongoDB/Redis는 엔진 구현과 테스트는 준비돼 있지만, Chat 이력 저장소 또는 Redis 기반 런타임 전환은 `src/rag_chatbot/api/chat/services/runtime.py` 조립 변경이 필요하다.
4. 파일 시스템 기반 로그 저장소(`FileLogRepository`)는 구현돼 있지만, 기본 런타임에 자동 조립되지는 않으므로 별도 주입이 필요하다.
5. 벡터 검색 백엔드는 ingestion 실행 시 `--backend`로 선택한다.

## 5. 채팅 이력 초기화

기본 저장소는 SQLite(`CHAT_DB_PATH`)다.

전체 파일 초기화:

```bash
rm -f data/db/chat/chat_history.sqlite
```

테이블 데이터만 삭제:

```bash
sqlite3 data/db/chat/chat_history.sqlite "DELETE FROM chat_messages; DELETE FROM chat_sessions;"
```

RAG 벡터 저장소 재적재가 필요하면 ingestion를 `--reset`으로 다시 실행한다.

```bash
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc --reset
```

## 6. 프로젝트 구조

### 6-1. 최상위 구조

```text
.
  src/rag_chatbot/
    api/                # HTTP 진입점, DTO, DI 조립
    core/               # 채팅 도메인 규칙과 그래프 조립
    shared/             # 공통 실행 인프라와 재사용 컴포넌트
    integrations/       # 외부 시스템 연동 어댑터
    resources/          # 런타임 환경별 리소스 파일
    static/             # 정적 UI 리소스
  ingestion/            # 문서 파싱/청킹/임베딩/업서트 파이프라인
  tests/                # pytest 테스트
  docs/                 # 코드 기준 상세 문서
  data/                 # 로컬 실행 데이터 경로
```

### 6-2. `src/rag_chatbot/` 디렉터리 레벨 책임 맵

| 경로 | 역할 | 구현 책임 범위 | 책임 밖 범위 |
| --- | --- | --- | --- |
| `src/rag_chatbot/api` | FastAPI 진입 계층 | 라우터 등록, 요청/응답 모델, HTTP 예외 변환, 런타임 의존성 주입 | 도메인 규칙 자체, DB 엔진 세부 구현 |
| `src/rag_chatbot/core` | 채팅 도메인 계층 | 상태 모델, 프롬프트, 노드 조립, 그래프 분기 규칙 | HTTP 프로토콜, 큐/버퍼 인프라 운영 |
| `src/rag_chatbot/shared` | 공용 실행 계층 | 서비스 오케스트레이션, 저장소, 메모리, 런타임 유틸리티, 공통 예외/로깅/설정 | 특정 외부 제품 API 세부 구현 |
| `src/rag_chatbot/integrations` | 외부 연동 계층 | LLM/Embedding/DB/파일 시스템 어댑터, 연결/매퍼/엔진 | 채팅 유스케이스 정책, API 라우팅 |
| `src/rag_chatbot/resources` | 환경 리소스 계층 | `dev/stg/prod`별 `.env` 파일 보관 | 런타임 로직 |
| `src/rag_chatbot/static` | 웹 UI 정적 리소스 계층 | HTML/CSS/JS, 아이콘, 프런트 상태 처리 | FastAPI 비즈니스 로직, 도메인 정책 |

### 6-3. `src/rag_chatbot/api` 하위 구조

```text
src/rag_chatbot/api/
  main.py               # 앱 엔트리, /ui 마운트, lifespan 종료 훅
  const/                # API prefix/path/tag 상수
  chat/                 # 비동기 Chat API
  ui/                   # UI 전용 세션/메시지 API
  health/               # 서버 상태 확인 API
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/rag_chatbot/api/chat/models` | Chat DTO | `/chat` 요청/응답 검증, SSE 구독 입력 모델 |
| `src/rag_chatbot/api/chat/routers` | Chat 라우터 | 작업 제출, 스트림 구독, 세션 스냅샷 조회 |
| `src/rag_chatbot/api/chat/services` | Chat 런타임 조립 | `ChatService`, `ServiceExecutor`, 큐/버퍼 싱글턴 조립 |
| `src/rag_chatbot/api/chat/utils` | Chat API 보조 유틸 | 도메인 모델을 API 응답 형태로 변환 |
| `src/rag_chatbot/api/ui/models` | UI DTO | 세션/메시지 목록 응답 모델 |
| `src/rag_chatbot/api/ui/routers` | UI 라우터 | 세션 생성, 조회, 삭제 엔드포인트 |
| `src/rag_chatbot/api/ui/services` | UI 서비스 | `ChatService` 결과를 UI 응답 모델로 매핑 |
| `src/rag_chatbot/api/ui/utils` | UI 매퍼 | 도메인 엔티티를 UI DTO로 변환 |
| `src/rag_chatbot/api/health` | Health API | `/health` 단일 엔드포인트와 응답 모델 관리 |

### 6-4. `src/rag_chatbot/core/chat` 하위 구조

```text
src/rag_chatbot/core/chat/
  const/                # 도메인 상수와 기본 메시지
  models/               # ChatSession, ChatMessage 같은 엔티티
  state/                # 그래프 상태 키 정의
  prompts/              # 시스템 프롬프트
  nodes/                # safeguard/context_strategy/RAG/response 노드 조립체
  graphs/               # LangGraph 그래프 조립
  utils/                # 도메인 <-> 문서 매핑 유틸
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/rag_chatbot/core/chat/const` | 도메인 설정값 | DB 경로, 기본 context window, 차단 메시지 |
| `src/rag_chatbot/core/chat/models` | 핵심 엔티티 | 세션, 메시지, 역할, 턴 결과 모델 정의 |
| `src/rag_chatbot/core/chat/state` | 그래프 상태 계약 | 노드 간 전달되는 상태 키의 타입 계약 |
| `src/rag_chatbot/core/chat/prompts` | 프롬프트 정책 | 일반 응답, safeguard, keyword, relevance, context strategy 프롬프트 관리 |
| `src/rag_chatbot/core/chat/nodes` | 도메인 노드 조립 | 실제 사용할 LLM/메시지/분기/RAG 노드 인스턴스 선언 |
| `src/rag_chatbot/core/chat/graphs` | 그래프 정의 | 노드 연결, 진입점, 조건 분기, stream 정책 설정 |
| `src/rag_chatbot/core/chat/utils` | 매핑 유틸 | 도메인 모델과 저장 문서 간 변환 지원 |

### 6-5. `src/rag_chatbot/shared` 하위 구조

```text
src/rag_chatbot/shared/
  chat/                 # 그래프 실행, 저장소, 메모리, 서비스
  runtime/              # 큐, 이벤트 버퍼, 워커, 스레드풀
  config/               # 설정/런타임 환경 로더
  logging/              # 공통 로거와 로그 저장소
  exceptions/           # 공통 예외 모델
  const/                # 공통 상수
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/rag_chatbot/shared/chat/interface` | 포트 계약 | 그래프, 서비스, 실행기 인터페이스 정의 |
| `src/rag_chatbot/shared/chat/graph` | 그래프 공통 실행기 | 그래프 컴파일, 이벤트 표준화, stream 필터링 |
| `src/rag_chatbot/shared/chat/nodes` | 재사용 노드 | `LLMNode`, `BranchNode`, `MessageNode`, `FanoutBranchNode` 같은 범용 노드 |
| `src/rag_chatbot/shared/chat/repositories` | 대화 이력 저장소 | 세션/메시지 CRUD, `request_id` 멱등 저장 관리 |
| `src/rag_chatbot/shared/chat/memory` | 세션 메모리 캐시 | 최근 메시지 컨텍스트 메모리 유지 |
| `src/rag_chatbot/shared/chat/services` | 서비스 계층 | `ChatService`, `ServiceExecutor` 실행 오케스트레이션 |
| `src/rag_chatbot/shared/runtime/queue` | 작업 큐 | InMemory/Redis 큐 인터페이스와 구현 |
| `src/rag_chatbot/shared/runtime/buffer` | 이벤트 버퍼 | SSE 이벤트 적재/소비 저장소 |
| `src/rag_chatbot/shared/runtime/worker` | 백그라운드 실행기 | 워커 모델과 실행 루프 지원 |
| `src/rag_chatbot/shared/runtime/thread_pool` | 스레드풀 유틸 | 비동기성 보조 스레드 실행 정책 |
| `src/rag_chatbot/shared/config` | 설정 로딩 | `.env`/JSON/환경 변수 병합 및 런타임 환경 해석 |
| `src/rag_chatbot/shared/logging` | 공통 로깅 | Logger, 로그 모델, 저장소 구현 |
| `src/rag_chatbot/shared/exceptions` | 공통 예외 | 코드/원인 추적이 가능한 애플리케이션 예외 정의 |

### 6-6. `src/rag_chatbot/integrations` 하위 구조

```text
src/rag_chatbot/integrations/
  llm/                  # LLM 클라이언트 래퍼
  embedding/            # 임베딩 클라이언트 래퍼
  db/                   # DB 클라이언트, 엔진, 쿼리 빌더
  fs/                   # 파일 시스템 저장소
```

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/rag_chatbot/integrations/llm` | LLM 연동 | LangChain 모델 래핑, 호출 로깅, 예외 표준화 |
| `src/rag_chatbot/integrations/embedding` | 임베딩 연동 | 임베딩 모델 래핑, 차원 정책 연결 |
| `src/rag_chatbot/integrations/db/base` | DB 공통 타입 | 엔진/세션/모델/쿼리 계약 |
| `src/rag_chatbot/integrations/db/query_builder` | 쿼리 빌더 | 읽기/쓰기/삭제 쿼리 조립 유틸 |
| `src/rag_chatbot/integrations/db/engines/sqlite` | SQLite 엔진 | 기본 Chat 저장소 엔진 |
| `src/rag_chatbot/integrations/db/engines/postgres` | PostgreSQL 엔진 | 관계형 저장 및 벡터 검색 지원 |
| `src/rag_chatbot/integrations/db/engines/mongodb` | MongoDB 엔진 | 문서 저장/조회 어댑터 |
| `src/rag_chatbot/integrations/db/engines/redis` | Redis 엔진 | keyspace 기반 저장/벡터 유틸 |
| `src/rag_chatbot/integrations/db/engines/elasticsearch` | Elasticsearch 엔진 | 인덱스 기반 검색 어댑터 |
| `src/rag_chatbot/integrations/db/engines/lancedb` | LanceDB 엔진 | 로컬 벡터 저장소 지원 |
| `src/rag_chatbot/integrations/fs/base` | 파일 저장소 계약 | 파일 엔진 인터페이스 |
| `src/rag_chatbot/integrations/fs/engines` | 파일 엔진 구현 | 로컬 파일 시스템 저장 구현 |

### 6-7. `ingestion`, `resources`, `static`

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `ingestion/ingest.py` | 통합 ingestion 엔트리 | CLI 인자 해석, 러너 실행 |
| `ingestion/core` | ingestion 핵심 로직 | 파일 파싱, 청킹, 주석 생성, 임베딩 조립 |
| `ingestion/steps` | 단계별 파이프라인 | chunk, embedding, backend upsert 단계 분리 |
| `src/rag_chatbot/resources/dev` | 개발 환경 리소스 | `ENV=dev`일 때 추가 로드할 `.env` 보관 |
| `src/rag_chatbot/resources/stg` | 스테이징 환경 리소스 | `ENV=stg`용 설정 보관 |
| `src/rag_chatbot/resources/prod` | 운영 환경 리소스 | `ENV=prod`용 설정 보관 |
| `src/rag_chatbot/static/index.html` | UI 엔트리 | 채팅 화면 골격 |
| `src/rag_chatbot/static/css` | 스타일 | 레이아웃/테마 정의 |
| `src/rag_chatbot/static/js/core` | 프런트 초기화 | 앱 부트스트랩과 전역 흐름 제어 |
| `src/rag_chatbot/static/js/chat` | 채팅 UI | 전송, 셀 렌더링, 스트림 반영 |
| `src/rag_chatbot/static/js/ui` | UI 제어 | 패널 토글, 그리드, 테마 관리 |
| `src/rag_chatbot/static/js/utils` | 프런트 유틸 | DOM, Markdown, 문법 하이라이팅 |
| `src/rag_chatbot/static/asset` | 정적 자산 | 아이콘, 로고 등 시각 리소스 |

## 7. 구현자가 먼저 이해해야 하는 경계

1. `api`는 HTTP 입출력 경계만 다루고, 채팅 규칙은 직접 구현하지 않는다.
2. `core`는 채팅 정책과 그래프 분기를 정의하지만, 큐/버퍼/DB 연결 세부 구현은 모른다.
3. `shared`는 `core`를 실제 서비스로 실행하기 위한 공통 실행기와 저장소를 제공한다.
4. `integrations`는 외부 기술 스택을 감싸지만, 어떤 유스케이스에서 호출할지는 결정하지 않는다.
5. `ingestion`은 검색용 문서 적재 파이프라인을 담당하며, 온라인 채팅 요청 처리 경로와 분리된다.
6. `static`은 `/ui-api/chat/*`, `/chat/*`를 소비하는 클라이언트이며 서버 정책의 소유자가 아니다.

## 8. 문서 인덱스

| 문서 | 링크 | 설명 |
| --- | --- | --- |
| 문서 허브 | [docs/README.md](docs/README.md) | 전체 맵, 변경 진입점 |
| Setup 개요 | [docs/setup/overview.md](docs/setup/overview.md) | 인프라/환경 문서 인덱스 |
| Setup ENV | [docs/setup/env.md](docs/setup/env.md) | `.env` 키 전체 설명, 로딩 순서 |
| Setup Ingestion | [docs/setup/ingestion.md](docs/setup/ingestion.md) | 통합 ingestion 실행/시퀀스 |
| Setup LanceDB | [docs/setup/lancedb.md](docs/setup/lancedb.md) | LanceDB 벡터 검색 구성 |
| Setup PostgreSQL | [docs/setup/postgresql_pgvector.md](docs/setup/postgresql_pgvector.md) | PostgreSQL + pgvector 설치/연동 |
| Setup MongoDB | [docs/setup/mongodb.md](docs/setup/mongodb.md) | MongoDB 설치/연동 |
| Setup FileSystem | [docs/setup/filesystem.md](docs/setup/filesystem.md) | 파일 시스템 로그 연동 |
| API 개요 | [docs/api/overview.md](docs/api/overview.md) | API 계층 책임/라우팅 |
| API Chat | [docs/api/chat.md](docs/api/chat.md) | `/chat` 인터페이스, SSE |
| API UI | [docs/api/ui.md](docs/api/ui.md) | `/ui-api/chat` 인터페이스 |
| API Health | [docs/api/health.md](docs/api/health.md) | `/health` 인터페이스 |
| Core 개요 | [docs/core/overview.md](docs/core/overview.md) | core 계층 문서 인덱스 |
| Core Chat | [docs/core/chat.md](docs/core/chat.md) | 그래프/노드 동작 |
| Shared 개요 | [docs/shared/overview.md](docs/shared/overview.md) | shared 계층 문서 인덱스 |
| Shared Chat | [docs/shared/chat/README.md](docs/shared/chat/README.md) | 실행기/저장/멱등 규칙 |
| Shared Runtime | [docs/shared/runtime.md](docs/shared/runtime.md) | Queue/EventBuffer 구성 |
| Shared Config | [docs/shared/config.md](docs/shared/config.md) | 설정/환경 로딩 |
| Shared Exceptions | [docs/shared/exceptions.md](docs/shared/exceptions.md) | 공통 예외 모델 |
| Shared Logging | [docs/shared/logging.md](docs/shared/logging.md) | 공통 로깅 저장소/정책 |
| Integrations 개요 | [docs/integrations/overview.md](docs/integrations/overview.md) | 연동 계층 문서 인덱스 |
| Integrations DB | [docs/integrations/db/README.md](docs/integrations/db/README.md) | DB 엔진/셋업 |
| Integrations LLM | [docs/integrations/llm/README.md](docs/integrations/llm/README.md) | `LLMClient` 사용 |
| Integrations Embedding | [docs/integrations/embedding/README.md](docs/integrations/embedding/README.md) | `EmbeddingClient` 사용 |
| Integrations FS | [docs/integrations/fs/README.md](docs/integrations/fs/README.md) | 파일 저장소 경로/정책 |
| Static UI | [docs/static/ui.md](docs/static/ui.md) | UI 연동 순서/상태 관리 |

## 9. 테스트

전체:

```bash
uv run pytest
```

E2E 예시:

```bash
uv run pytest tests/e2e/test_chat_api_server_e2e.py -q
```

정적 분석 예시:

```bash
uv run ty check src
uv run ruff format src -v
uv run ruff clean
```
