# Integrations DB 문서

`src/text_to_sql/integrations/db` 모듈을 코드 파일 단위로 정리한 문서 허브다.

## 1. 문서 범위

- 대상 모듈 수: `44` (`__init__.py` 제외)
- 문서 경로는 소스 상대경로와 1:1로 매핑한다.

## 2. 모듈 목록

- [base/engine.md](base/engine.md)
- [base/models.md](base/models.md)
- [base/pool.md](base/pool.md)
- [base/query_builder.md](base/query_builder.md)
- [base/session.md](base/session.md)
- [client.md](client.md)
- [engines/elasticsearch/connection.md](engines/elasticsearch/connection.md)
- [engines/elasticsearch/document_mapper.md](engines/elasticsearch/document_mapper.md)
- [engines/elasticsearch/engine.md](engines/elasticsearch/engine.md)
- [engines/elasticsearch/filter_builder.md](engines/elasticsearch/filter_builder.md)
- [engines/elasticsearch/schema_manager.md](engines/elasticsearch/schema_manager.md)
- [engines/lancedb/document_mapper.md](engines/lancedb/document_mapper.md)
- [engines/lancedb/engine.md](engines/lancedb/engine.md)
- [engines/lancedb/filter_engine.md](engines/lancedb/filter_engine.md)
- [engines/lancedb/schema_adapter.md](engines/lancedb/schema_adapter.md)
- [engines/mongodb/connection.md](engines/mongodb/connection.md)
- [engines/mongodb/document_mapper.md](engines/mongodb/document_mapper.md)
- [engines/mongodb/engine.md](engines/mongodb/engine.md)
- [engines/mongodb/filter_builder.md](engines/mongodb/filter_builder.md)
- [engines/mongodb/schema_manager.md](engines/mongodb/schema_manager.md)
- [engines/postgres/condition_builder.md](engines/postgres/condition_builder.md)
- [engines/postgres/connection.md](engines/postgres/connection.md)
- [engines/postgres/document_mapper.md](engines/postgres/document_mapper.md)
- [engines/postgres/engine.md](engines/postgres/engine.md)
- [engines/postgres/schema_manager.md](engines/postgres/schema_manager.md)
- [engines/postgres/vector_adapter.md](engines/postgres/vector_adapter.md)
- [engines/postgres/vector_store.md](engines/postgres/vector_store.md)
- [engines/redis/connection.md](engines/redis/connection.md)
- [engines/redis/document_mapper.md](engines/redis/document_mapper.md)
- [engines/redis/engine.md](engines/redis/engine.md)
- [engines/redis/filter_evaluator.md](engines/redis/filter_evaluator.md)
- [engines/redis/keyspace.md](engines/redis/keyspace.md)
- [engines/redis/vector_scorer.md](engines/redis/vector_scorer.md)
- [engines/sql_common.md](engines/sql_common.md)
- [engines/sqlite/condition_builder.md](engines/sqlite/condition_builder.md)
- [engines/sqlite/connection.md](engines/sqlite/connection.md)
- [engines/sqlite/document_mapper.md](engines/sqlite/document_mapper.md)
- [engines/sqlite/engine.md](engines/sqlite/engine.md)
- [engines/sqlite/schema_manager.md](engines/sqlite/schema_manager.md)
- [query_builder/aggregate_read_builder.md](query_builder/aggregate_read_builder.md)
- [query_builder/delete_builder.md](query_builder/delete_builder.md)
- [query_builder/read_builder.md](query_builder/read_builder.md)
- [query_builder/write_builder.md](query_builder/write_builder.md)
- [query_target_registry.md](query_target_registry.md)

## 3. 관련 문서

- `docs/integrations/overview.md`
- `docs/README.md`
