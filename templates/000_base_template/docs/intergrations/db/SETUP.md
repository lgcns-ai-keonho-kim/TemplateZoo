# DB 설치 및 환경 구성

이 문서는 로컬 개발 환경에서 DB 엔진을 실행하고 `.env`를 구성하는 절차를 정의한다.

## 공통 준비

```bash
cp .env.sample .env
uv venv .venv
uv sync
```

## SQLite

Chat 기본 저장소는 SQLite다.

```env
CHAT_DB_PATH=data/db/chat/chat_history.sqlite
SQLITE_DB_DIR=data/db
SQLITE_DB_PATH=data/db/playground.sqlite
```

### sqlite-vec 사용 환경

벡터 검색을 사용하려면 loadable extension이 가능한 Python 빌드가 필요하다.

```bash
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.13.9
pyenv local 3.13.9
```

## PostgreSQL + PGVector

### 컨테이너 실행

```bash
docker run -d \
  --name template-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=playground \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### 확장 활성화

```bash
sudo -u postgres psql -d playground
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 환경 변수

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PW=postgres
POSTGRES_DATABASE=playground
POSTGRES_ENABLE_VECTOR=1
# POSTGRES_DSN=postgresql://postgres:postgres@127.0.0.1:5432/playground
```

## Redis

### 컨테이너 실행

```bash
docker run -d \
  --name template-redis \
  -p 6379:6379 \
  redis:7
```

### 환경 변수

```env
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PW=
# REDIS_URL=redis://127.0.0.1:6379/0
```

## MongoDB

### 컨테이너 실행

```bash
docker run -d \
  --name template-mongodb \
  -p 27017:27017 \
  mongo:7
```

### 환경 변수

```env
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
MONGODB_USER=
MONGODB_PW=
MONGODB_DB=playground
MONGODB_AUTH_DB=
# MONGODB_URI=mongodb://127.0.0.1:27017
```

## Elasticsearch

### 개발용 단일 노드

```bash
docker run -d \
  --name template-elasticsearch \
  -p 9200:9200 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  docker.elastic.co/elasticsearch/elasticsearch:8.15.2
```

### 환경 변수

```env
ELASTICSEARCH_SCHEME=http
ELASTICSEARCH_HOST=127.0.0.1
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=
ELASTICSEARCH_PW=
ELASTICSEARCH_CA_CERTS=
ELASTICSEARCH_VERIFY_CERTS=false
ELASTICSEARCH_SSL_FINGERPRINT=
# ELASTICSEARCH_HOSTS=http://127.0.0.1:9200
```

### HTTPS/TLS 환경

```env
ELASTICSEARCH_SCHEME=https
ELASTICSEARCH_CA_CERTS=certs/http_ca.crt
ELASTICSEARCH_VERIFY_CERTS=true
```

## Chat/LLM 핵심 변수

```env
CHAT_LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
CHAT_DB_PATH=data/db/chat/chat_history.sqlite
CHAT_MEMORY_MAX_MESSAGES=200
CHAT_TASK_MAX_WORKERS=4
```

## 서버 실행

```bash
uv run uvicorn base_template.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 연결 확인 포인트

1. `/health`가 `200`을 반환해야 한다.
2. `/chat/sessions` 세션 생성이 성공해야 한다.
3. `/chat/sessions/{session_id}/queue` 호출 후 `task_id`가 반환되어야 한다.
4. `/chat/sessions/{session_id}/tasks/{task_id}/stream`에서 `token` 이벤트가 수신되어야 한다.
