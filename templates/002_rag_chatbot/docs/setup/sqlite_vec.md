# SQLite + sqlite-vec 구성 가이드

이 문서는 SQLite 저장소와 `sqlite-vec` 확장을 이 프로젝트에 연결하는 절차를 정리한다.
특히 데이터 파일의 기본 저장 위치와 벡터 테이블이 어디에 생성되는지에 초점을 맞춘다.

## 1. 적용 범위

1. 로컬 단일 노드에서 빠르게 Chat 저장소를 띄우는 경우
2. PostgreSQL 전환 전 SQLite로 기능 검증을 먼저 진행하는 경우
3. SQLite 벡터 검색(`vec0`) 실험이 필요한 경우

## 2. 관련 스크립트

| 경로 | 역할 |
| --- | --- |
| `src/rag_chatbot/core/chat/const/settings.py` | Chat 기본 DB 파일 경로(`CHAT_DB_PATH`) 정의 |
| `src/rag_chatbot/shared/chat/repositories/history_repository.py` | 기본 저장소 조립 (SQLiteEngine + DBClient) |
| `src/rag_chatbot/integrations/db/engines/sqlite/engine.py` | SQLite CRUD/쿼리/벡터 검색 엔진 |
| `src/rag_chatbot/integrations/db/engines/sqlite/connection.py` | SQLite 연결/PRAGMA/sqlite-vec 로딩 |
| `src/rag_chatbot/integrations/db/engines/sqlite/schema_manager.py` | 컬렉션/벡터 테이블 생성 |
| `src/rag_chatbot/integrations/db/engines/sqlite/vector_store.py` | `vec0` 가상 테이블 관리 및 벡터 검색 |

## 3. 데이터 저장 기본 위치

### 3-1. Chat 기본 저장 파일

기본 Chat 저장 파일 경로:

- `data/db/chat/chat_history.sqlite`

결정 근거:

1. `CHAT_DB_PATH` 기본값이 `data/db/chat/chat_history.sqlite`
2. `ChatHistoryRepository`가 `db_client` 미주입 시 해당 경로로 SQLiteEngine 생성

### 3-2. 범용 SQLiteEngine 기본 파일

직접 `SQLiteEngine()`를 생성할 때 기본 경로:

- `data/db/playground.sqlite`

### 3-3. sqlite-vec 벡터 테이블 위치

벡터 테이블은 별도 파일이 아니라 **같은 SQLite 파일 내부**에 생성된다.

생성 규칙:

1. 테이블명 기본값: `vec_<collection>`
2. 스키마에서 `vector_table`을 지정하면 그 이름 사용
3. 가상 테이블 타입: `vec0`

정리:

1. Chat 기본 모드에서는 `enable_vector=False`라 벡터 테이블이 생성되지 않는다.
2. 벡터 검색을 켜면 기본 DB 파일 내부에 `vec_*` 테이블이 추가된다.

## 4. 선행 조건

### 4-1. Python 런타임 요구사항

`sqlite-vec`를 Python에서 사용하려면 단순 패키지 설치 외에 런타임 조건이 맞아야 한다.

1. 현재 프로젝트 기준 Python 버전은 `>=3.13`이어야 한다(`pyproject.toml` 기준).
2. `sqlite3.Connection.enable_load_extension(...)`을 호출할 수 있어야 한다.
3. 런타임에 포함된 SQLite 버전은 3.41+를 권장한다.

핵심:

1. `sqlite-vec` 설치만으로는 충분하지 않다.
2. Python의 `sqlite3` 모듈이 확장 로딩을 지원하지 않으면 벡터 확장 로드에 실패한다.

### 4-2. 기본 설치 절차 (권장 순서)

아래 순서로 먼저 설치/검증한다.

```bash
uv python install 3.13
uv venv --python 3.13
source .venv/bin/activate
uv sync
```

확장 로딩 지원 여부 확인:

```bash
uv run python - <<'PY'
import sqlite3

conn = sqlite3.connect(":memory:")
print("enable_load_extension 메서드 존재:", hasattr(conn, "enable_load_extension"))
conn.enable_load_extension(True)
conn.enable_load_extension(False)
print("확장 로딩 토글: OK")
PY
```

`sqlite-vec` 로딩 확인:

```bash
uv run python - <<'PY'
import sqlite3
import sqlite_vec

conn = sqlite3.connect(":memory:")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
print("sqlite_vec 버전:", conn.execute("select vec_version()").fetchone()[0])
PY
```

### 4-3. `enable_load_extension` 미지원 시 재설치 경로

#### macOS

공식 가이드 기준으로 Homebrew Python 사용을 권장한다.

```bash
brew install python
uv venv --python "$(brew --prefix)/bin/python3"
source .venv/bin/activate
uv sync
```

#### Linux/공통 (소스 빌드 기반)

Python을 직접 빌드할 수 있는 환경에서는 `--enable-loadable-sqlite-extensions` 옵션으로 설치한다.
`pyenv`를 사용할 경우 아래처럼 설치할 수 있다.

```bash
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.13.2
pyenv local 3.13.2
uv venv --python 3.13.2
source .venv/bin/activate
uv sync
```

### 4-4. 환경 파일/디렉터리 준비

1. `.env` 파일 준비: 최소 `CHAT_DB_PATH`, `SQLITE_BUSY_TIMEOUT_MS` 점검
2. 쓰기 가능한 디렉터리 권한 확인: `data/db/*`

참고:

1. `sqlite-vec` 패키지가 없으면 `SQLiteEngine(enable_vector=True)` 연결 시 `RuntimeError`가 발생한다.
2. `enable_load_extension` 미지원 런타임이면 `sqlite_vec.load(...)` 단계에서 실패한다.

## 5. 기본 Chat 저장소 동작

현재 기본 동작은 아래와 같다.

1. `runtime.py`에서 `ChatHistoryRepository()`를 직접 생성
2. `ChatHistoryRepository` 내부에서 `SQLiteEngine(enable_vector=False)` 생성
3. Chat 세션/메시지/request 커밋 컬렉션을 SQLite에 저장

즉, 기본 Chat API는 SQLite를 사용하지만 벡터 검색은 사용하지 않는다.

## 6. sqlite-vec 활성화 절차

### 6-1. DB 경로/타임아웃 설정

```env
CHAT_DB_PATH=data/db/chat/chat_history.sqlite
SQLITE_BUSY_TIMEOUT_MS=5000
```

### 6-2. 벡터 컬럼 스키마를 갖는 엔진 조립

```python
from rag_chatbot.integrations.db import DBClient
from rag_chatbot.integrations.db.base import CollectionSchema, ColumnSpec
from rag_chatbot.integrations.db.engines.sqlite import SQLiteEngine

engine = SQLiteEngine(
    database_path="data/db/playground.sqlite",
    enable_vector=True,
)
client = DBClient(engine)

schema = CollectionSchema(
    name="documents",
    primary_key="doc_id",
    vector_field="embedding",
    vector_dimension=1536,
    columns=[
        ColumnSpec(name="doc_id", is_primary=True, nullable=False),
        ColumnSpec(name="title"),
        ColumnSpec(name="embedding", is_vector=True, dimension=1536),
    ],
)

client.connect()
client.create_collection(schema)
```

### 6-3. 생성 확인 포인트

1. SQLite 파일이 지정 경로에 생성되는지 확인한다.
2. 메인 테이블(`documents`)과 벡터 테이블(`vec_documents`)이 함께 생성되는지 확인한다.
3. 벡터 검색 호출 시 `supports_vector_search=True`인지 확인한다.

## 7. 운영 관점 권장사항

1. Chat 기본 저장소 파일(`CHAT_DB_PATH`)과 벡터 실험용 파일을 분리한다.
2. 백업 시 `.sqlite` 파일 단위 백업 정책을 사용한다.
3. 다중 프로세스 동시 쓰기가 많아지면 PostgreSQL 전환을 우선 검토한다.
4. `SQLITE_BUSY_TIMEOUT_MS`를 지나치게 낮게 주지 않는다.

## 8. 장애 대응

| 증상 | 원인 후보 | 확인 경로 | 조치 |
| --- | --- | --- | --- |
| `sqlite-vec 패키지가 설치되어 있지 않습니다.` | 의존성 누락 | `sqlite/connection.py` | `uv sync` 후 재실행 |
| 벡터 검색이 항상 실패 | `enable_vector=False` | `history_repository.py`, 엔진 조립 코드 | 벡터 모드 엔진으로 재조립 |
| DB 파일 생성 실패 | 디렉터리 권한 문제 | `CHAT_DB_PATH` 값, OS 권한 | 상위 디렉터리 생성/권한 부여 |
| 잠금 오류가 자주 발생 | timeout 과소, 동시성 과다 | `SQLITE_BUSY_TIMEOUT_MS` | timeout 조정, 쓰기 패턴 재검토 |

## 9. 소스 매칭 체크리스트

1. 기본 저장 위치 설명이 `core/chat/const/settings.py`와 일치하는가
2. 벡터 테이블 생성 규칙이 `sqlite/vector_store.py`와 일치하는가
3. 기본 Chat에서 `enable_vector=False` 설명이 `history_repository.py`와 일치하는가
4. sqlite-vec 로딩 실패 조건이 `sqlite/connection.py`와 일치하는가

## 10. 관련 문서

- `docs/setup/env.md`
- `docs/integrations/db.md`
- `docs/shared/chat.md`
