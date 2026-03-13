# Setup 개요

`docs/setup` 하위 문서의 구성과 적용 대상을 정리한 개요다.

## 1. 문서 구성

| 문서 | 주요 내용 | 사용 상황 |
| --- | --- | --- |
| `docs/setup/env.md` | `.env` 키 설명과 실제 반영 위치 확인 | 프로젝트 초기 부트스트랩, 배포 전 변수 점검 |
| `docs/setup/mongodb.md` | MongoDB 설치, 인증, 엔진 연동 절차 | MongoDB 엔진 검증/전환 시 |
| `docs/setup/filesystem.md` | 파일 시스템 기반 로그 저장소 연동 방식 | 로그 영속화/파일 백엔드 확장 시 |

## 2. 대표 문서

1. `docs/setup/env.md`
2. `README.md`
3. `docs/integrations/db/query_target_registry.md`

## 3. 최소 실행 경로 (로컬 단일 노드)

1. `.env`를 생성하고 `GEMINI_MODEL`, `GEMINI_PROJECT`, `TABLE_ALLOWLIST_FILE`, `POSTGRES_*`를 설정한다.
2. `table_allowlist.yaml`에서 PostgreSQL target alias, `database`, `schema`, 테이블/컬럼 설명을 정의한다.
3. 서버를 실행하고 `/health`, `/docs`, `/ui`를 순서대로 점검한다.

startup 흐름:

1. allowlist 로드 + allowlist 대상 introspection이 선행된다.
2. introspection 실패 시 서버는 fail-fast로 시작에 실패한다.
3. query target registry는 startup에 등록되지만, 실제 DB 연결은 첫 조회 시점에 lazy connect 된다.

예시:

```bash
uv run uvicorn text_to_sql.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. 확장 실행 경로

### 4-1. PostgreSQL

1. PostgreSQL 서버와 계정/권한을 준비한다.
2. `table_allowlist` target에 `engine: postgres`와 `connection`을 정의한다.
3. `connection.*_env`를 사용한다면 `.env`에 해당 `POSTGRES_*` 값을 설정한다.
4. 같은 인스턴스를 쓰더라도 `database`가 다르면 target별로 allowlist 항목을 나눈다.
5. 서버 startup에서 introspection이 통과하는지 확인한다.

### 4-2. MongoDB

1. MongoDB 서버와 계정/인증 DB를 준비한다.
2. `table_allowlist` target에 `engine: mongodb`와 `connection`을 정의한다.
3. `connection.*_env`를 사용한다면 `.env`에 해당 `MONGODB_*` 값을 설정한다.
4. 서버 startup에서 introspection이 통과하는지 확인한다.

### 4-3. 파일 시스템 로그 저장

1. 로그 기준 디렉터리(`data/logs` 등)를 설계한다.
2. `FileLogRepository(base_dir=...)`를 주입해 로그 저장소를 활성화한다.
3. 운영 정책(보관 기간, 아카이빙 경로, 접근 권한)을 확정한다.

## 5. 코드 매핑

| 설정 영역 | 관련 코드 |
| --- | --- |
| 런타임 환경 로딩 | `src/text_to_sql/shared/config/runtime_env_loader.py`, `src/text_to_sql/api/main.py` |
| Chat 런타임 변수 소비 | `src/text_to_sql/api/chat/services/runtime.py`, `src/text_to_sql/shared/chat/services/chat_service.py` |
| 기본 SQLite 저장소 | `src/text_to_sql/shared/chat/repositories/history_repository.py`, `src/text_to_sql/core/chat/const/settings.py` |
| allowlist 로드/정규화 | `src/text_to_sql/core/chat/utils/table_allowlist_loader.py` |
| startup introspection | `src/text_to_sql/core/chat/utils/schema_introspection.py` |
| target registry/lazy connect | `src/text_to_sql/integrations/db/query_target_registry.py`, `src/text_to_sql/integrations/db/engines/postgres/connection.py` |
| PostgreSQL | `src/text_to_sql/integrations/db/engines/postgres/*.py` |
| MongoDB | `src/text_to_sql/integrations/db/engines/mongodb/*.py` |
| 파일 시스템 연동 | `src/text_to_sql/integrations/fs/*.py`, `src/text_to_sql/shared/logging/logger.py` |
