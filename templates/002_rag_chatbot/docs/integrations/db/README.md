# Integrations DB 문서 개요

이 문서는 `src/rag_chatbot/integrations/db` 하위 모듈의 책임과 문서 인덱스를 제공한다.

## 1. 구조

```text
src/rag_chatbot/integrations/db/
  client.py
  base/*.py
  query_builder/*.py
  engines/sql_common.py
  engines/elasticsearch/*.py
  engines/lancedb/*.py
  engines/mongodb/*.py
  engines/postgres/*.py
  engines/redis/*.py
  engines/sqlite/*.py
```

## 2. 핵심 흐름

1. `client.py`가 DB 엔진 호출을 단일 인터페이스로 제공한다.
2. `base/*.py`와 `query_builder/*.py`가 Query/Schema/DSL 공통 규약을 정의한다.
3. `engines/*`가 저장소별 실제 CRUD/검색 구현을 담당한다.

## 3. 문서 인덱스

- `docs/integrations/db/base/engine.md`
- `docs/integrations/db/base/models.md`
- `docs/integrations/db/base/pool.md`
- `docs/integrations/db/base/query_builder.md`
- `docs/integrations/db/base/session.md`
- `docs/integrations/db/client.md`
- `docs/integrations/db/engines/elasticsearch/connection.md`
- `docs/integrations/db/engines/elasticsearch/document_mapper.md`
- `docs/integrations/db/engines/elasticsearch/engine.md`
- `docs/integrations/db/engines/elasticsearch/filter_builder.md`
- `docs/integrations/db/engines/elasticsearch/schema_manager.md`
- `docs/integrations/db/engines/lancedb/document_mapper.md`
- `docs/integrations/db/engines/lancedb/engine.md`
- `docs/integrations/db/engines/lancedb/filter_engine.md`
- `docs/integrations/db/engines/lancedb/schema_adapter.md`
- `docs/integrations/db/engines/mongodb/connection.md`
- `docs/integrations/db/engines/mongodb/document_mapper.md`
- `docs/integrations/db/engines/mongodb/engine.md`
- `docs/integrations/db/engines/mongodb/filter_builder.md`
- `docs/integrations/db/engines/mongodb/schema_manager.md`
- `docs/integrations/db/engines/postgres/condition_builder.md`
- `docs/integrations/db/engines/postgres/connection.md`
- `docs/integrations/db/engines/postgres/document_mapper.md`
- `docs/integrations/db/engines/postgres/engine.md`
- `docs/integrations/db/engines/postgres/schema_manager.md`
- `docs/integrations/db/engines/postgres/vector_adapter.md`
- `docs/integrations/db/engines/postgres/vector_store.md`
- `docs/integrations/db/engines/redis/connection.md`
- `docs/integrations/db/engines/redis/document_mapper.md`
- `docs/integrations/db/engines/redis/engine.md`
- `docs/integrations/db/engines/redis/filter_evaluator.md`
- `docs/integrations/db/engines/redis/keyspace.md`
- `docs/integrations/db/engines/redis/vector_scorer.md`
- `docs/integrations/db/engines/sql_common.md`
- `docs/integrations/db/engines/sqlite/condition_builder.md`
- `docs/integrations/db/engines/sqlite/connection.md`
- `docs/integrations/db/engines/sqlite/document_mapper.md`
- `docs/integrations/db/engines/sqlite/engine.md`
- `docs/integrations/db/engines/sqlite/schema_manager.md`
- `docs/integrations/db/query_builder/delete_builder.md`
- `docs/integrations/db/query_builder/read_builder.md`
- `docs/integrations/db/query_builder/write_builder.md`

## 4. 관련 문서

- `docs/integrations/overview.md`
- `docs/setup/lancedb.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
