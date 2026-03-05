# Setup 가이드 개요

이 문서는 `docs/setup` 하위 환경/인프라 설정 문서를 빠르게 탐색하기 위한 인덱스입니다.

## 1. 문서 구성

| 문서 | 목적 | 열어야 하는 시점 |
| --- | --- | --- |
| `docs/setup/env.md` | `.env` 키 설명과 실제 반영 위치 확인 | 프로젝트 초기 부트스트랩, 배포 전 변수 점검 |
| `docs/setup/lancedb.md` | LanceDB 구성과 파일 기반 벡터 저장 경로 정리 | 로컬 벡터 엔진 실험 시 |
| `docs/setup/postgresql_pgvector.md` | PostgreSQL + pgvector 설치/초기화/연동 절차 | 운영형 DB/벡터 저장 전환 시 |
| `docs/setup/mongodb.md` | MongoDB 설치, 인증, 엔진 연동 절차 | MongoDB 엔진 검증/전환 시 |
| `docs/setup/filesystem.md` | 파일 시스템 기반 로그 저장소 연동 방식 | 로그 영속화/파일 백엔드 확장 시 |

주의:

- 현재 템플릿은 Chat 런타임과 API 서버 구성에 집중되어 있습니다.

## 2. 권장 읽기 순서

1. `docs/setup/env.md`
2. `docs/setup/lancedb.md`
3. `docs/setup/postgresql_pgvector.md`
4. `docs/setup/mongodb.md`
5. `docs/setup/filesystem.md`

## 3. 최소 실행 경로 (로컬 단일 노드)

1. `.env`를 생성하고 `GEMINI_MODEL`, `GEMINI_PROJECT`, `CHAT_DB_PATH`를 설정합니다.
2. 서버를 실행하고 `/health`, `/docs`, `/ui`를 순서대로 점검합니다.

예시:

```bash
uv run uvicorn plan_and_then_execute_agent.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. 확장 실행 경로

### 4-1. PostgreSQL + pgvector

1. PostgreSQL 서버와 pgvector 확장을 설치합니다.
2. DB/계정/권한을 준비하고 `.env`에 `POSTGRES_*` 값을 넣습니다.
3. 벡터 저장소를 PostgreSQL로 옮길 때는 `integrations/db/engines/postgres`를 주입합니다.
4. Chat 이력 저장까지 PostgreSQL로 옮기려면 `api/chat/services/runtime.py`의 저장소 조립을 변경합니다.

### 4-2. MongoDB

1. MongoDB 서버와 계정/인증 DB를 준비합니다.
2. `.env`에 `MONGODB_*` 값을 설정합니다.
3. `runtime.py`에서 MongoDB 엔진을 주입해 Chat 저장소를 교체합니다.

### 4-3. 파일 시스템 로그 저장

1. 로그 기준 디렉터리(`data/logs` 등)를 설계합니다.
2. 예시 경로를 사용할 때는 서비스 시작 전에 권한/마운트 정책을 먼저 확인합니다.
3. `FileLogRepository(base_dir=...)`를 주입해 로그 저장소를 활성화합니다.
4. 운영 정책(보관 기간, 아카이빙 경로, 접근 권한)을 확정합니다.

## 5. 코드 매핑

| 설정 영역 | 관련 코드 |
| --- | --- |
| 런타임 환경 로딩 | `shared/config/runtime_env_loader.py`, `api/main.py` |
| Chat 런타임 변수 소비 | `api/chat/services/runtime.py`, `shared/chat/services/chat_service.py` |
| 기본 SQLite 저장소 | `shared/chat/repositories/history_repository.py`, `core/chat/const/settings.py` |
| LanceDB 벡터 엔진 | `integrations/db/engines/lancedb/*.py` |
| PostgreSQL/pgvector | `integrations/db/engines/postgres/*.py` |
| MongoDB | `integrations/db/engines/mongodb/*.py` |
| 파일 시스템 연동 | `integrations/fs/*.py`, `shared/logging/logger.py`, `shared/logging/_log_repository_interface.py` |

## 6. 문서 동기화 체크리스트

1. 문서에 적힌 환경 변수 키가 `.env.sample` 또는 코드(`os.getenv`)와 일치하는지 확인합니다.
2. SQLite 기본 경로 설명이 `CHAT_DB_PATH` 기본값과 일치하는지 확인합니다.
3. PostgreSQL/MongoDB 전환 예시가 `ChatHistoryRepository(db_client=...)` 패턴과 일치하는지 확인합니다.
