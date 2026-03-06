# Integrations DB 모듈 레퍼런스

`src/chatbot/integrations/db` 구조를 파일 단위 문서로 정리한 인덱스다.

## 1. 디렉터리 매핑

| 코드 경로 | 문서 |
| --- | --- |
| `src/chatbot/integrations/db/client.py` | `docs/integrations/db/client.md` |
| `src/chatbot/integrations/db/base/*.py` | `docs/integrations/db/base/*.md` |
| `src/chatbot/integrations/db/query_builder/*.py` | `docs/integrations/db/query_builder/*.md` |
| `src/chatbot/integrations/db/engines/sql_common.py` | `docs/integrations/db/engines/sql_common.md` |
| `src/chatbot/integrations/db/engines/*/*.py` | `docs/integrations/db/engines/*/*.md` |

## 2. 공개 API (`db/__init__.py`)

1. `DBClient`
2. `ReadBuilder`, `WriteBuilder`, `DeleteBuilder`
3. 엔진 구현체: `ElasticsearchEngine`, `LanceDBEngine`, `MongoDBEngine`, `PostgresEngine`, `RedisEngine`, `SQLiteEngine`

## 3. base 레이어 문서

- `docs/integrations/db/base/engine.md`
- `docs/integrations/db/base/models.md`
- `docs/integrations/db/base/pool.md`
- `docs/integrations/db/base/query_builder.md`
- `docs/integrations/db/base/session.md`

## 4. query_builder 레이어 문서

- `docs/integrations/db/query_builder/read_builder.md`
- `docs/integrations/db/query_builder/write_builder.md`
- `docs/integrations/db/query_builder/delete_builder.md`

## 5. 엔진 레이어 문서

### 5-1. SQLite

- `docs/integrations/db/engines/sqlite/engine.md`
- `docs/integrations/db/engines/sqlite/connection.md`
- `docs/integrations/db/engines/sqlite/condition_builder.md`
- `docs/integrations/db/engines/sqlite/document_mapper.md`
- `docs/integrations/db/engines/sqlite/schema_manager.md`

### 5-2. PostgreSQL

- `docs/integrations/db/engines/postgres/engine.md`
- `docs/integrations/db/engines/postgres/connection.md`
- `docs/integrations/db/engines/postgres/condition_builder.md`
- `docs/integrations/db/engines/postgres/document_mapper.md`
- `docs/integrations/db/engines/postgres/schema_manager.md`
- `docs/integrations/db/engines/postgres/vector_adapter.md`
- `docs/integrations/db/engines/postgres/vector_store.md`

### 5-3. MongoDB

- `docs/integrations/db/engines/mongodb/engine.md`
- `docs/integrations/db/engines/mongodb/connection.md`
- `docs/integrations/db/engines/mongodb/document_mapper.md`
- `docs/integrations/db/engines/mongodb/filter_builder.md`
- `docs/integrations/db/engines/mongodb/schema_manager.md`

### 5-4. Redis

- `docs/integrations/db/engines/redis/engine.md`
- `docs/integrations/db/engines/redis/connection.md`
- `docs/integrations/db/engines/redis/document_mapper.md`
- `docs/integrations/db/engines/redis/filter_evaluator.md`
- `docs/integrations/db/engines/redis/keyspace.md`
- `docs/integrations/db/engines/redis/vector_scorer.md`

### 5-5. LanceDB

- `docs/integrations/db/engines/lancedb/engine.md`
- `docs/integrations/db/engines/lancedb/document_mapper.md`
- `docs/integrations/db/engines/lancedb/filter_engine.md`
- `docs/integrations/db/engines/lancedb/schema_adapter.md`

### 5-6. Elasticsearch

- `docs/integrations/db/engines/elasticsearch/engine.md`
- `docs/integrations/db/engines/elasticsearch/connection.md`
- `docs/integrations/db/engines/elasticsearch/document_mapper.md`
- `docs/integrations/db/engines/elasticsearch/filter_builder.md`
- `docs/integrations/db/engines/elasticsearch/schema_manager.md`

### 5-7. 공통 SQL 유틸

- `docs/integrations/db/engines/sql_common.md`

## 6. 관련 문서

- `docs/integrations/overview.md`
- `docs/setup/sqlite.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/setup/troubleshooting.md`
