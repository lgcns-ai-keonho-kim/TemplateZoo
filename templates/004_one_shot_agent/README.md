# One Shot Agent

LLM 기반 1회성 Agent 실행 애플리케이션이다.
권장 Python 버전은 `3.13+`이다.

`RuntimeEnvironmentLoader`로 환경을 로드한 뒤 `intent_classify -> intent_prepare -> response` 그래프를 실행한다.
기본 런타임은 `Gemini LLM 노드 + AgentService` 조합이며, `POST /agent` 요청 1건에 대해 `run_id`, `status`, `output_text`를 반환한다.
기본 런타임은 세션 저장, Tool 실행, SSE 중계, 임베딩/벡터 검색을 사용하지 않는다.

## 1. 빠른 시작

### 1-1. 가상환경/의존성 설치

```bash
uv venv .venv
uv sync --group dev
```

### 1-2. 환경 변수 파일 생성

기본 로컬 실행:

```bash
cp .env.sample .env
```

기본 실행에 필요한 예시는 아래와 같다.

```env
ENV=local
LOG_STDOUT=1

GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_PROJECT=your-gcp-project-id
GEMINI_API_KEY=

AGENT_REQUEST_TIMEOUT_SECONDS=180
```

런타임 환경이 `dev/stg/prod`인 경우에는 루트 `.env` 외에 환경별 리소스 파일도 함께 준비한다.

예시(`dev`):

```bash
cp src/one_shot_agent/resources/dev/.env.sample src/one_shot_agent/resources/dev/.env
```

`RuntimeEnvironmentLoader`는 아래 순서로 환경을 로드한다.

1. 프로젝트 루트 `.env`
2. `ENV` / `APP_ENV` / `APP_STAGE` 해석
3. 값이 비어 있으면 `local`
4. 필요 시 `src/one_shot_agent/resources/<env>/.env`

### 1-3. 서버 실행

```bash
uv run python -m uvicorn --app-dir src one_shot_agent.api.main:app --host 0.0.0.0 --port 8000 --reload
```

서버는 아래 순서로 준비된다.

1. `api/main.py`가 `RuntimeEnvironmentLoader`로 루트 `.env`와 환경별 `.env`를 먼저 로드한다.
2. 환경 로드 이후 Agent/Health 라우터와 정적 UI를 import 및 등록한다.
3. `api/agent/services/runtime.py`가 `agent_graph`와 `AgentService`를 조립한다.

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 정적 UI: `http://127.0.0.1:8000/ui`

## 2. API 인터페이스 요약

### 2-1. Agent API

| Method | Path | 상태코드 | 설명 |
| --- | --- | --- | --- |
| `POST` | `/agent` | `200` | 요청 1건 실행 후 최종 결과 반환 |

요청 예시:

```json
{
  "request": "김대리에게 일정 조율 메일 초안 작성해줘."
}
```

응답 예시:

```json
{
  "run_id": "c4f1...",
  "status": "COMPLETED",
  "output_text": "최종 응답 본문"
}
```

오류 응답:

| 코드 | HTTP | 설명 |
| --- | --- | --- |
| `AGENT_REQUEST_EMPTY` | `400` | 요청 본문이 비어 있음 |
| `AGENT_REQUEST_TIMEOUT` | `504` | 요청 처리 시간 초과 |
| `AGENT_RESPONSE_EMPTY` | `500` | 실행 결과 본문이 비어 있음 |
| `AGENT_EXECUTION_CONFIG_INVALID` | `500` | 실행 설정이 올바르지 않음 |

### 2-2. Health API

| Method | Path | 상태코드 | 설명 |
| --- | --- | --- | --- |
| `GET` | `/health` | `200` | 서버 생존 상태 확인 |

### 2-3. UI 경로

| Method | Path | 상태코드 | 설명 |
| --- | --- | --- | --- |
| `GET` | `/ui` | `200` | 단일 요청 입력과 결과 확인 화면 |

## 3. 동작 방식

요청은 세션 저장 없이 독립적으로 처리한다.

1. 클라이언트가 `POST /agent`로 요청 1건을 보낸다.
2. 라우터가 요청 본문을 검증하고 `AgentService`를 호출한다.
3. 그래프가 `intent_classify -> intent_prepare -> response` 순서로 실행된다.
4. `AgentService`가 실행 결과를 집계해 단일 응답을 반환한다.
5. `/ui`는 `status`, `run_id`, `output_text`를 화면에 반영한다.

지원 요청 유형:

| 유형 | 설명 |
| --- | --- |
| `SUMMARY` | 입력 내용을 요약한다. |
| `TRANSLATION` | 번역 요청을 처리한다. |
| `FORMAT_WRITING` | 특정 형식의 글쓰기를 생성한다. |
| `GENERAL` | 일반 질의응답을 처리한다. |

정적 UI는 아래 흐름으로 동작한다.

1. 좌측 패널에서 요청을 작성한다.
2. `Run` 버튼으로 `POST /agent`를 호출한다.
3. 우측 패널에서 `status`, `run_id`, `output_text`를 확인한다.
4. 최종 응답은 결과 영역에 마크다운으로 렌더링된다.

## 4. 환경 변수 (`.env`)

기본 샘플은 `.env.sample`이다.
전체 키 설명과 로딩 우선순위는 `docs/setup/env.md`를 참고한다.
DB/벡터/임베딩 엔진은 `integrations` 레이어에 남아 있으며, 기본 런타임이 아니라 optional integrations 검증 경로로 본다.
`shared/runtime`의 `queue`, `worker`, `thread_pool` 유틸도 코드상 보존되어 있지만, 기본 `/agent` 런타임에는 포함되지 않는다.

### 4-1. 런타임/로그

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ENV` | `local` | 런타임 환경 선택 |
| `LOG_STDOUT` | `1` | stdout 로그 출력 여부 |

### 4-2. LLM

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `GEMINI_MODEL` | - | Agent 실행에 사용할 모델명 |
| `GEMINI_PROJECT` | - | Gemini 프로젝트 식별자 |
| `GEMINI_API_KEY` | - | Gemini 인증에 사용하는 API 키 |

### 4-3. Agent 실행

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `AGENT_REQUEST_TIMEOUT_SECONDS` | `180` | 요청 처리 타임아웃(초) |

### 4-4. 선택적 통합/테스트 키

아래 값은 기본 `/agent` 런타임이 아니라 optional integrations 검증에서만 사용한다.

| 범주 | 키 |
| --- | --- |
| PostgreSQL | `POSTGRES_*`, `POSTGRES_DSN`, `POSTGRES_ENABLE_VECTOR` |
| MongoDB | `MONGODB_*`, `MONGODB_URI` |
| Redis | `REDIS_*`, `REDIS_URL` |
| Elasticsearch | `ELASTICSEARCH_*`, `ELASTICSEARCH_HOSTS` |
| SQLite | `SQLITE_BUSY_TIMEOUT_MS` |

## 5. 프로젝트 구조

### 5-1. 최상위 구조

```text
.
  src/one_shot_agent/
    api/                # HTTP 진입점과 라우터
    core/               # Agent 그래프와 도메인 로직
    shared/             # 공용 서비스, 설정, 예외, 로깅
    integrations/       # 외부 시스템 연동 모듈
    resources/          # 환경별 리소스 파일
    static/             # 정적 UI 리소스
  tests/                # pytest 테스트
  docs/                 # 코드 기준 상세 문서
  data/                 # 로컬 실행 데이터 경로
```

### 5-2. 디렉터리 책임 맵

| 경로 | 역할 | 구현 책임 범위 |
| --- | --- | --- |
| `src/one_shot_agent/api` | FastAPI 진입 계층 | 라우터 등록, 요청/응답 모델, HTTP 예외 변환 |
| `src/one_shot_agent/core` | Agent 도메인 계층 | 그래프 흐름, 노드 조립, 실행 규칙 |
| `src/one_shot_agent/shared` | 공용 실행 계층 | `AgentService`, 설정 로더, 예외, 로깅 |
| `src/one_shot_agent/shared/runtime` | 보존 유틸 계층 | 선택적 `queue`/`worker`/`thread_pool` 유틸 |
| `src/one_shot_agent/integrations` | 외부 연동 계층 | LLM, DB, 파일 시스템, 임베딩 어댑터 |
| `src/one_shot_agent/resources` | 환경 리소스 계층 | `dev/stg/prod`별 `.env.sample` 보관 |
| `src/one_shot_agent/static` | 정적 UI 계층 | HTML, CSS, JS, 아이콘 |
| `tests` | 테스트 계층 | API, core, integrations, shared 검증 |

## 6. 관련 문서

| 문서 | 링크 | 설명 |
| --- | --- | --- |
| 문서 허브 | [docs/README.md](docs/README.md) | 전체 문서 맵과 확인 순서 |
| Setup 개요 | [docs/setup/overview.md](docs/setup/overview.md) | 환경·인프라 문서 인덱스 |
| Setup ENV | [docs/setup/env.md](docs/setup/env.md) | `.env` 키 설명과 로딩 순서 |
| API 개요 | [docs/api/overview.md](docs/api/overview.md) | 공개 경로와 API 계층 책임 |
| API Agent | [docs/api/agent.md](docs/api/agent.md) | `/agent` 요청/응답 계약 |
| API Health | [docs/api/health.md](docs/api/health.md) | `/health` 인터페이스 |
| Core Agent | [docs/core/agent.md](docs/core/agent.md) | 그래프 흐름과 의도 처리 |
| Shared Agent | [docs/shared/agent/overview.md](docs/shared/agent/overview.md) | 공용 Agent 실행 계층 |
| Static UI | [docs/static/ui.md](docs/static/ui.md) | UI 동작과 화면 구성 |

## 7. 테스트

전체 테스트:

```bash
uv run pytest
```

빠른 검증:

```bash
uv run python -m pytest tests/api/test_agent_routes.py tests/core/agent/nodes/test_intent_prepare_node.py
uv run ty check src
```
