# BASE TEMPLATE

LLM 기반 애플리케이션을 빠르게 시작하기 위한 Python/FastAPI 템플릿이다.  
권장 Python 버전은 `3.13+`이다.

## 1. 빠른 시작

### 1-1. 프로젝트명 초기화(선택)

```bash
bash init.sh my-project
```

- 단일 인자를 받는다.
- 내부에서 자동 변환:
- `PROJECT_SLUG`: `my-project`
- `PACKAGE_NAME`: `my_project`

### 1-2. 가상환경/의존성 설치

```bash
uv venv .venv
uv sync
```

### 1-3. 환경 변수 파일 생성

```bash
cp .env.sample .env
```

필수 값 예시:

```env
GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_PROJECT=...
GEMINI_EMBEDDING_DIM=1024
```

## 2. 서버 실행

```bash
uv run uvicorn rag_chatbot.api.main:app --host 0.0.0.0 --port 8000 --reload
```

`.env`는 `RuntimeEnvironmentLoader`가 자동 로드한다.

접속 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `http://127.0.0.1:8000/health`
- 정적 UI: `http://127.0.0.1:8000/ui`

## 3. API 인터페이스 요약

### 3-1. Chat API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/chat` | 채팅 작업 제출 (`session_id`, `message`, `context_window`) |
| `GET` | `/chat/{session_id}` | 세션 스냅샷(메시지/최근 상태) 조회 |
| `GET` | `/chat/{session_id}/events?request_id=...` | 요청 단위 SSE 이벤트 구독 |

### 3-2. UI API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/ui-api/chat/sessions` | UI 세션 생성 |
| `GET` | `/ui-api/chat/sessions` | UI 세션 목록 |
| `GET` | `/ui-api/chat/sessions/{session_id}/messages` | UI 메시지 목록 |
| `DELETE` | `/ui-api/chat/sessions/{session_id}` | 세션+메시지 삭제 |

## 4. 실행 흐름

현재 시스템은 `세션 + 비동기 실행 + SSE` 구조로 동작한다.

1. UI는 `/ui-api/chat/sessions`로 세션 목록을 가져오고 활성 세션을 정한다.
2. 사용자가 메시지를 보내면 `POST /chat`을 호출한다.
3. 서버는 `session_id`, `request_id`, `status=QUEUED`를 즉시 반환한다.
4. UI는 `GET /chat/{session_id}/events?request_id=...`로 스트림을 구독한다.
5. `ServiceExecutor`가 큐를 소비하며 `start -> token* -> references? -> done/error` 이벤트를 보낸다.
6. 완료 시 assistant 응답은 `request_id` 멱등 기준으로 저장된다.

## 5. Ingestion 빠른 실행

통합 ingestion 엔트리포인트는 `ingestion/ingest.py` 하나다.

```bash
# LanceDB
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc

# PostgreSQL
uv run python ingestion/ingest.py --backend postgres --input-root data/ingestion-doc

# Elasticsearch
uv run python ingestion/ingest.py --backend elasticsearch --input-root data/ingestion-doc
```

자주 쓰는 옵션:

- `--sample`: 확장자별 1개 파일만 처리
- `--chunk-workers`: 청킹 워커 수 지정
- `--reset`: 기존 `rag_chunks` 삭제 후 재생성

예시:

```bash
uv run python ingestion/ingest.py --backend lancedb --input-root data/ingestion-doc --reset
```

상세 시퀀스는 `docs/setup/ingestion.md`를 참고한다.

## 6. 환경 변수 (`.env`)

기본 샘플: `.env.sample`

전체 키 상세 설명과 반영 상태는 `docs/setup/env.md`를 참고한다.

### 6-1. 런타임/로그

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `ENV` | (빈값) | `local/dev/stg/prod` 런타임 선택 |
| `LOG_STDOUT` | `1` | stdout JSON 로그 출력 여부 |

### 6-2. Chat/RAG 핵심

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `GEMINI_MODEL` | `.env.sample` 기준 `gemini-3.1-flash-lite-preview` | Gemini 채팅 모델명 |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Gemini 임베딩 모델명 |
| `GEMINI_PROJECT` | (빈값) | Gemini 프로젝트 ID |
| `GEMINI_EMBEDDING_DIM` | `1024` | 임베딩 차원 (양의 정수) |
| `CHAT_DB_PATH` | `data/db/chat/chat_history.sqlite` | Chat 이력 SQLite 경로 |

참고:

- 기본 노드(`core/chat/nodes/*.py`)와 ingestion runner는 `GEMINI_*`를 사용한다.
- ingestion/RAG 벡터 검색은 `GEMINI_EMBEDDING_DIM`으로 차원을 맞춘다.

## 7. 채팅 이력 초기화

기본 저장소는 SQLite(`CHAT_DB_PATH`)다.

전체 파일 초기화:

```bash
rm -f data/db/chat/chat_history.sqlite
```

테이블 데이터만 삭제:

```bash
sqlite3 data/db/chat/chat_history.sqlite "DELETE FROM chat_messages; DELETE FROM chat_sessions;"
```

## 8. 프로젝트 구조

```text
src/rag_chatbot/
  api/                  # FastAPI 라우터, DTO, DI 조립
  core/
    chat/               # 도메인 모델, 그래프, 노드, 프롬프트
  shared/
    chat/               # ChatService/ServiceExecutor/Repository/Memory
    runtime/            # Queue/EventBuffer/Worker/ThreadPool
    logging/            # 공통 로깅
    config/             # 설정/환경 로더
    exceptions/         # 공통 예외
    const/              # 공통 상수
  integrations/         # DB/LLM/Embedding/FS 외부 연동 어댑터
  static/               # 정적 UI
ingestion/              # 문서 파싱/청킹/임베딩/적재 파이프라인
tests/                  # pytest 테스트
docs/                   # 개발 문서
```

## 9. 문서 인덱스

| 문서 | 링크 | 설명 |
| --- | --- | --- |
| 문서 허브 | [docs/README.md](docs/README.md) | 전체 맵, 변경 진입점 |
| Setup 개요 | [docs/setup/overview.md](docs/setup/overview.md) | 인프라/환경 문서 인덱스 |
| Setup ENV | [docs/setup/env.md](docs/setup/env.md) | `.env` 키 상세 설명 |
| Setup Ingestion | [docs/setup/ingestion.md](docs/setup/ingestion.md) | 통합 ingestion 실행/시퀀스 |
| Setup LanceDB | [docs/setup/lancedb.md](docs/setup/lancedb.md) | 파일 기반 LanceDB 구성 |
| Setup PostgreSQL | [docs/setup/postgresql_pgvector.md](docs/setup/postgresql_pgvector.md) | PostgreSQL + pgvector 설치/연동 |
| Setup MongoDB | [docs/setup/mongodb.md](docs/setup/mongodb.md) | MongoDB 설치/연동 |
| Setup FileSystem | [docs/setup/filesystem.md](docs/setup/filesystem.md) | 파일 시스템 로그 연동 |
| API Chat | [docs/api/chat.md](docs/api/chat.md) | `/chat` 인터페이스, SSE |
| Core Chat | [docs/core/chat.md](docs/core/chat.md) | 그래프/노드 동작 |
| Integrations DB | [docs/integrations/db.md](docs/integrations/db.md) | DB 엔진/셋업 |
| Integrations LLM | [docs/integrations/llm.md](docs/integrations/llm.md) | `LLMClient` 사용 |
| Integrations Embedding | [docs/integrations/embedding.md](docs/integrations/embedding.md) | `EmbeddingClient` 사용 |

## 10. 테스트

전체:

```bash
uv run pytest
```

E2E 예시:

```bash
uv run pytest tests/e2e/test_chat_api_server_e2e.py -v -s
```
