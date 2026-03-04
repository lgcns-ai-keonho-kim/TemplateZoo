# PostgreSQL + pgvector 구성 가이드

이 문서는 PostgreSQL 설치부터 pgvector 확장 활성화, 그리고 이 프로젝트에 연동하는 단계까지 정리한다.

## 1. 적용 범위

1. ingestion 백엔드를 PostgreSQL로 전환해 `rag_chunks`를 저장할 때
2. PostgreSQL 벡터 검색(`vector`, `ivfflat`) 사용 준비
3. Chat 저장소를 SQLite에서 PostgreSQL로 바꾸는 확장 경로 확인

## 2. 관련 코드

| 경로 | 역할 |
| --- | --- |
| `ingestion/ingest.py` | 통합 ingestion CLI |
| `ingestion/steps/upsert_postgres_step.py` | PostgreSQL 업서트 + `--reset` 처리 |
| `ingestion/core/db.py` | PostgreSQL 클라이언트/스키마/차원 검증 |
| `src/rag_chatbot/integrations/db/engines/postgres/engine.py` | PostgreSQL 엔진 |
| `src/rag_chatbot/integrations/db/engines/postgres/connection.py` | psycopg2 연결/pgvector 등록 |
| `src/rag_chatbot/integrations/db/engines/postgres/vector_store.py` | 확장/인덱스 처리 |
| `src/rag_chatbot/api/chat/services/runtime.py` | Chat 저장소 조립 지점 |

## 3. 설치 방법

아래 중 한 가지 방식으로 설치한다.

### 3-1. Docker 기반 (빠른 검증)

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
# 예: postgresql-16-pgvector, postgresql-15-pgvector
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

확인 포인트:

1. `\dx` 결과에 `vector`가 보여야 한다.
2. 애플리케이션 계정이 `CREATE TABLE`, `CREATE INDEX` 권한을 가져야 한다.

## 5. 환경 변수

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
POSTGRES_DATABASE=playground
# 선택: 한 줄 DSN
# POSTGRES_DSN=postgresql://postgres:postgres@127.0.0.1:5432/playground
```

## 6. ingestion 연동

PostgreSQL 벡터 저장을 사용하려면 ingestion를 `postgres` 백엔드로 실행한다.

```bash
uv run python ingestion/ingest.py --backend postgres --input-root data/ingestion-doc
```

재적재 예시:

```bash
uv run python ingestion/ingest.py --backend postgres --input-root data/ingestion-doc --reset
```

`--reset`은 기존 `rag_chunks` 테이블을 삭제 후 재생성한다.

## 7. Chat 저장소 전환(선택)

현재 기본 Chat 저장소는 SQLite다. Chat 이력까지 PostgreSQL로 옮기려면 `runtime.py` 조립을 바꾼다.

예시:

```python
import os

from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.engines.postgres import PostgresEngine
from rag_chatbot.shared.chat import ChatHistoryRepository

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

## 8. 장애 대응

| 증상 | 원인 후보 | 조치 |
| --- | --- | --- |
| `psycopg2-binary 패키지가 설치되어 있지 않습니다.` | 의존성 누락 | `uv sync` 후 재실행 |
| `type "vector" does not exist` | pgvector 확장 미설치 | `CREATE EXTENSION vector` 실행 |
| `INGESTION_EMBEDDING_DIMENSION_MISMATCH` | 기존 벡터 차원 불일치 | `--reset` 후 재적재 |
| 연결은 되지만 테이블 생성 실패 | DB 권한 부족 | 계정 권한(`CREATE`, `USAGE`) 부여 |
| DSN/호스트 설정 혼선 | `POSTGRES_DSN` 우선 적용 | DSN 또는 분리 키 중 하나로 통일 |

## 9. 운영 체크리스트

1. `POSTGRES_*` 값을 `dev/stg/prod`별로 분리한다.
2. 비밀번호/접속정보는 시크릿 스토어로 관리한다.
3. 차원 정책(`GEMINI_EMBEDDING_DIM`) 변경 시 재적재 절차를 운영 문서에 포함한다.
4. ingestion 상세 시퀀스는 `docs/setup/ingestion.md`를 함께 참조한다.

## 10. 관련 문서

- `docs/setup/env.md`
- `docs/setup/ingestion.md`
- `docs/setup/lancedb.md`
- `docs/integrations/db.md`
