# PostgreSQL + pgvector 구성 가이드

이 문서는 PostgreSQL 설치부터 pgvector 확장 활성화, 그리고 이 프로젝트 저장소에 주입하는 단계까지 정리한다.
목표는 SQLite 기본 저장소를 PostgreSQL 기반으로 교체해도 코드 수정 범위를 최소화하는 것이다.

## 1. 적용 범위

1. Chat 저장소를 파일 기반(SQLite)에서 서버형 DB로 전환
2. PostgreSQL 벡터 검색(`vector` 타입, `ivfflat`) 사용 준비
3. 운영 환경에서 연결/권한/확장 설치 절차 표준화

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/base_template/api/chat/services/runtime.py` | 저장소 조립 지점 (PostgreSQL 주입 예시 포함) |
| `src/base_template/shared/chat/repositories/history_repository.py` | `db_client` 주입형 저장소 |
| `src/base_template/integrations/db/engines/postgres/engine.py` | PostgreSQL 엔진 |
| `src/base_template/integrations/db/engines/postgres/connection.py` | psycopg2 연결/pgvector 타입 등록 |
| `src/base_template/integrations/db/engines/postgres/schema_manager.py` | 테이블 생성/컬럼 변경 |
| `src/base_template/integrations/db/engines/postgres/vector_store.py` | `CREATE EXTENSION vector`, 인덱스 생성 |

## 3. 설치 방법

아래 중 한 가지 방식으로 설치한다.

### 3-1. Docker 기반 (가장 빠른 검증)

```bash
docker run --name pg-playground \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=playground \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

### 3-2. Ubuntu/Debian 패키지 기반

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
# PostgreSQL 버전에 맞는 pgvector 패키지를 설치한다.
# 예: postgresql-16-pgvector, postgresql-15-pgvector
sudo apt install -y postgresql-16-pgvector
```

### 3-3. macOS(Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16
brew install pgvector
```

## 4. DB/계정/확장 초기화

```bash
# 필요 시 postgres 계정으로 접속
psql -U postgres -h 127.0.0.1 -p 5432

# psql 내부
CREATE DATABASE playground;
\c playground
CREATE EXTENSION IF NOT EXISTS vector;
\dx
```

확인 포인트:

1. `\dx` 결과에 `vector`가 보여야 한다.
2. 애플리케이션 계정이 `CREATE TABLE`, `CREATE INDEX` 권한을 가져야 한다.

## 5. 환경 변수 설정

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
POSTGRES_DATABASE=playground
# 선택: 한 줄 DSN
# POSTGRES_DSN=postgresql://postgres:postgres@127.0.0.1:5432/playground
```

벡터 테스트를 수행할 때만:

```env
POSTGRES_ENABLE_VECTOR=1
```

## 6. 프로젝트 연동 절차

현재 기본 조립은 SQLite다. PostgreSQL을 쓰려면 런타임 조립을 교체한다.

1. `src/base_template/api/chat/services/runtime.py`에서 PostgreSQL 예시 블록을 활성화한다.
2. `PostgresEngine` -> `DBClient` -> `ChatHistoryRepository(db_client=...)` 순서로 주입한다.
3. 서버 재시작 후 세션 생성/메시지 저장 동작을 확인한다.

예시 코드:

```python
import os

from base_template.integrations.db import DBClient
from base_template.integrations.db.engines.postgres import PostgresEngine
from base_template.shared.chat import ChatHistoryRepository

postgres_engine = PostgresEngine(
    dsn=(os.getenv("POSTGRES_DSN") or "").strip() or None,
    host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=(os.getenv("POSTGRES_PW") or "").strip() or None,
    database=os.getenv("POSTGRES_DATABASE", "playground"),
)

history_repository = ChatHistoryRepository(
    db_client=DBClient(postgres_engine),
)
```

## 7. pgvector 동작 포인트

1. 스키마에 벡터 컬럼이 있으면 `CREATE EXTENSION IF NOT EXISTS vector`를 호출한다.
2. 벡터 컬럼 인덱스는 `ivfflat (vector_cosine_ops)`로 생성된다.
3. 벡터 컬럼이 없는 스키마에서는 pgvector 확장 의존이 없다.

주의사항:

1. 현재 Chat 기본 스키마(세션/메시지/커밋)는 벡터 컬럼이 없다.
2. 즉, Chat 저장만 PostgreSQL로 옮길 때는 pgvector 인덱스가 자동 생성되지 않는다.
3. 벡터 검색을 쓰려면 별도 컬렉션 스키마(`vector_field`, `vector_dimension`)를 설계해야 한다.

## 8. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| `psycopg2-binary 패키지가 설치되어 있지 않습니다.` | 의존성 누락 | `postgres/connection.py` | `uv sync` 재실행 |
| 연결은 되지만 테이블 생성 실패 | DB 권한 부족 | DB 권한, 서버 로그 | 계정 권한 부여(`CREATE`, `USAGE`) |
| 벡터 쿼리 시 `type "vector" does not exist` | pgvector 확장 미설치 | `\dx`, `CREATE EXTENSION` 실행 여부 | 확장 설치 후 재시도 |
| DSN/호스트 설정 혼선 | `POSTGRES_DSN` 우선 적용 | `.env`, 런타임 조립 코드 | DSN 또는 분리 키 중 하나로 통일 |

## 9. 운영 전 체크리스트

1. `POSTGRES_*` 값이 런타임 환경별(`dev/stg/prod`)로 분리되어 있는가
2. 비밀번호/접속정보가 시크릿 스토어로 관리되는가
3. 연결 실패/재시도/모니터링 로그가 수집되는가
4. 스키마 마이그레이션 절차(DDL 반영 순서)가 정의되어 있는가

## 10. 관련 문서

- `docs/setup/env.md`
- `docs/integrations/db.md`
- `docs/shared/chat.md`
