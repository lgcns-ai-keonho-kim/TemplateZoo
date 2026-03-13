# Setup 개요

`docs/setup`은 현재 기본 `/agent` 런타임을 실행하는 방법과, 선택적 인프라 확장 경로를 구분해 안내한다.

## 1. 문서 구성

| 문서 | 목적 | 사용 맥락 |
| --- | --- | --- |
| `docs/setup/env.md` | 기본 런타임 환경 변수 확인 | 로컬 실행, 배포 전 변수 점검 |
| `docs/setup/lancedb.md` | 벡터 엔진 실험 참고 | 선택적 인프라 실험 |
| `docs/setup/postgresql_pgvector.md` | PostgreSQL/pgvector 실험 참고 | DB 엔진 검증, 수동 조립 |
| `docs/setup/mongodb.md` | MongoDB 엔진 실험 참고 | DB 엔진 검증, 수동 조립 |
| `docs/setup/filesystem.md` | 파일 기반 로그 저장 연동 | 로그 영속화 확장 |

## 2. 최소 실행 경로

1. `.env`를 만들고 `GEMINI_MODEL`, `GEMINI_PROJECT`, `AGENT_REQUEST_TIMEOUT_SECONDS`를 설정한다.
2. 현재 소스 우선순위로 서버를 실행한다.
3. `/health`, `/docs`, `/ui`를 순서대로 확인한다.

예시:

```bash
PYTHONPATH=src uv run uvicorn single_request_tool_agent.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 3. 현재 기본 런타임 특성

1. 공개 API는 `/agent`, `/health`, `/ui`만 제공한다.
2. 세션/대화 이력, SSE, 작업 큐는 기본 실행 경로에서 사용하지 않는다.
3. `AgentService`가 그래프 이벤트를 내부 집계해 단일 JSON 응답을 반환한다.

## 4. 선택적 확장 경로

### 4-1. PostgreSQL + pgvector

벡터 엔진 테스트나 수동 저장소 조립에 사용할 수 있다. 현재 기본 `/agent` 런타임이 자동으로 활성화하지는 않는다.

### 4-2. MongoDB

MongoDB 엔진 테스트와 수동 저장소 조립 예시는 가능하지만, 현재 기본 `/agent` 런타임은 이를 직접 사용하지 않는다.

### 4-3. 파일 시스템 로그 저장

`FileLogRepository`를 별도로 주입해 로그를 파일에 저장하는 확장은 유지된다.

## 5. 코드 매핑

| 설정 영역 | 관련 코드 |
| --- | --- |
| 런타임 환경 로딩 | `shared/config/runtime_env_loader.py`, `api/main.py` |
| 기본 Agent 런타임 | `api/agent/services/runtime.py`, `shared/agent/services/agent_service.py` |
| 그래프 조립 | `core/agent/graphs/chat_graph.py` |
| 기본 Tool 등록 | `core/agent/tools/registry.py` |
| 정적 UI | `static/index.html`, `static/js/agent/app.js` |
