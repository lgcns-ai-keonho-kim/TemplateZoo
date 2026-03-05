# PostgreSQL + pgvector 구성 가이드

이 문서는 PostgreSQL 설치부터 pgvector 확장 활성화, 그리고 프로젝트에 연동하는 단계까지 정리합니다.

## 1. 적용 범위

1. PostgreSQL 벡터 검색(`vector`, `ivfflat`) 사용 준비
2. DB 엔진 테스트/실험
3. Chat 저장소를 SQLite에서 PostgreSQL로 바꾸는 확장 경로 확인

## 2. 관련 코드

| 경로 | 역할 |
| --- | --- |
| `src/plan_and_then_execute_agent/integrations/db/engines/postgres/engine.py` | PostgreSQL 엔진 |
| `src/plan_and_then_execute_agent/integrations/db/engines/postgres/connection.py` | psycopg2 연결/pgvector 등록 |
| `src/plan_and_then_execute_agent/integrations/db/engines/postgres/vector_store.py` | 확장/인덱스 처리 |
| `src/plan_and_then_execute_agent/api/chat/services/runtime.py` | Chat 저장소 조립 지점 |
| `tests/integrations/db/Vector/test_postgres_engine_vector.py` | PostgreSQL 벡터 테스트 |

## 3. 설치 방법

### 3-1. Docker 기반

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
sudo apt install -y postgresql-16-pgvector
```

### 3-3. macOS(Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16
brew install pgvector
```

## 4. DB/확장 초기화

```bash
psql -U postgres -h 127.0.0.1 -p 5432

# psql 내부
CREATE DATABASE playground;
\c playground
CREATE EXTENSION IF NOT EXISTS vector;
\dx
```

## 5. 환경 변수

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
POSTGRES_DATABASE=playground
# POSTGRES_DSN=postgresql://postgres:postgres@127.0.0.1:5432/playground
```

## 6. Chat 저장소 전환(선택)

현재 기본 Chat 저장소는 SQLite입니다.
Chat 이력을 PostgreSQL로 옮기려면 `runtime.py` 조립을 변경합니다.

```python
import os

from plan_and_then_execute_agent.integrations.db import DBClient
from plan_and_then_execute_agent.integrations.db.engines.postgres import PostgresEngine
from plan_and_then_execute_agent.shared.chat import ChatHistoryRepository

postgres_engine = PostgresEngine(
    dsn=(os.getenv("POSTGRES_DSN") or "").strip() or None,
    host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=(os.getenv("POSTGRES_PW") or "").strip() or None,
    database=os.getenv("POSTGRES_DATABASE", "playground"),
)

history_repository = ChatHistoryRepository(db_client=DBClient(postgres_engine))
```

## 7. 빠른 검증 절차

```bash
uv run pytest tests/integrations/db/CRUD/test_postgres_engine_crud.py -q
uv run pytest tests/integrations/db/Vector/test_postgres_engine_vector.py -q
```

## 8. 장애 대응

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| `psycopg2-binary 패키지가 설치되어 있지 않습니다.` | 의존성 누락 | `uv sync` 후 재실행 |
| `type "vector" does not exist` | pgvector 확장 미설치 | `CREATE EXTENSION vector` 실행 |
| 연결은 되지만 테이블 생성 실패 | DB 권한 부족 | 계정 권한(`CREATE`, `USAGE`) 부여 |
| DSN/호스트 설정 혼선 | `POSTGRES_DSN` 우선 적용 | DSN 또는 분리 키 중 하나로 통일 |

## 9. 관련 문서

- `docs/setup/env.md`
- `docs/integrations/db.md`
