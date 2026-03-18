# Setup 개요

`docs/setup` 하위 환경·인프라 문서의 역할과 사용 맥락을 묶어 정리한다.

## 1. 문서 구성

| 문서 | 목적 | 사용 맥락 |
| --- | --- | --- |
| `docs/setup/env.md` | 루트 `.env`와 optional integration 키 설명 | 프로젝트 초기 부트스트랩, 배포 전 변수 점검 |
| `docs/setup/lancedb.md` | LanceDB 엔진 실험 절차 | optional integration 검증 시 |
| `docs/setup/postgresql_pgvector.md` | PostgreSQL + pgvector 설치/검증 절차 | optional integration 검증 시 |
| `docs/setup/mongodb.md` | MongoDB 설치, 인증, 엔진 연동 절차 | optional integration 검증 시 |
| `docs/setup/filesystem.md` | 파일 시스템 기반 로그 저장소 연동 방식 | 로그 영속화/파일 백엔드 확장 시 |

주의:

- 현재 템플릿의 기본 런타임은 단일 요청 Agent와 API 서버 구성에 집중되어 있다.
- DB/벡터/임베딩 관련 문서는 기본 런타임이 아니라 optional integrations 검증 경로다.
- `shared/runtime`의 `queue`, `worker`, `thread_pool`는 보존 유틸이며 기본 `/agent` 런타임 조립에는 포함되지 않는다.

## 2. 핵심 문서 흐름

1. `docs/setup/env.md`
2. `docs/setup/lancedb.md`
3. `docs/setup/postgresql_pgvector.md`
4. `docs/setup/mongodb.md`
5. `docs/setup/filesystem.md`

## 3. 최소 실행 경로 (로컬 단일 노드)

1. `.env`를 생성하고 `GEMINI_MODEL`, `GEMINI_PROJECT`를 설정합니다.
2. 서버를 실행하고 `/health`, `/docs`, `/ui`를 순서대로 점검합니다.

예시:

```bash
uv run uvicorn single_request_agent.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. 확장 실행 경로

### 4-1. PostgreSQL + pgvector

1. PostgreSQL 서버와 pgvector 확장을 설치합니다.
2. DB/계정/권한을 준비하고 `.env`에 `POSTGRES_*` 값을 넣습니다.
3. 현재 기본 `/agent` 런타임은 이 엔진을 자동으로 사용하지 않습니다.
4. 엔진 검증이나 커스텀 조립이 필요할 때만 `integrations/db/engines/postgres`를 직접 사용합니다.

### 4-2. MongoDB

1. MongoDB 서버와 계정/인증 DB를 준비합니다.
2. `.env`에 `MONGODB_*` 값을 설정합니다.
3. 현재는 엔진 검증 또는 커스텀 조립 용도로만 사용합니다.

### 4-3. 파일 시스템 로그 저장

1. 로그 기준 디렉터리(`data/logs` 등)를 설계합니다.
2. 예시 경로를 사용할 때는 서비스 시작 전에 권한/마운트 정책을 먼저 확인합니다.
3. `FileLogRepository(base_dir=...)`를 주입해 로그 저장소를 활성화합니다.
4. 운영 정책(보관 기간, 아카이빙 경로, 접근 권한)을 확정합니다.

## 5. 코드 매핑

| 설정 영역 | 관련 코드 |
| --- | --- |
| 런타임 환경 로딩 | `shared/config/runtime_env_loader.py`, `api/main.py` |
| Agent 런타임 변수 소비 | `api/agent/services/runtime.py`, `core/agent/nodes/*.py` |
| LanceDB 벡터 엔진 | `integrations/db/engines/lancedb/*.py` |
| PostgreSQL/pgvector | `integrations/db/engines/postgres/*.py` |
| MongoDB | `integrations/db/engines/mongodb/*.py` |
| 파일 시스템 연동 | `integrations/fs/*.py`, `shared/logging/logger.py`, `shared/logging/_log_repository_interface.py` |
