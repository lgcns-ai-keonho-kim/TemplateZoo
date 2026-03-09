# db/engines/postgres/engine.md

소스 경로: `src/text_to_sql/integrations/db/engines/postgres/engine.py`

## 1. 역할

- 목적: PostgreSQL 기반 DB 엔진을 제공한다.
- 설명: 컬렉션 스키마 기반 CRUD와 PGVector 벡터 검색을 처리한다.
- 디자인 패턴: 어댑터 패턴

## 2. 주요 구성

### 2-1. 클래스

| 클래스 | 핵심 메서드 |
| --- | --- |
| `PostgresEngine` | `__init__, name, supports_vector_search, connect, close, create_collection, delete_collection, add_column, ...` |

### 2-2. 함수

- 정의된 최상위 함수가 없다.

## 3. 오류/예외 코드

- 모듈 내부에서 명시적으로 정의한 오류 코드가 없다.

## 4. 연관 모듈

- `src/text_to_sql/integrations/db/base/engine.py`
- `src/text_to_sql/shared/logging/__init__.py`
- `src/text_to_sql/integrations/db/base/models.py`
- `src/text_to_sql/integrations/db/engines/sql_common.py`
- `src/text_to_sql/integrations/db/engines/postgres/condition_builder.py`
- `src/text_to_sql/integrations/db/engines/postgres/connection.py`
- `src/text_to_sql/integrations/db/engines/postgres/document_mapper.py`
- `src/text_to_sql/integrations/db/engines/postgres/schema_manager.py`
- `src/text_to_sql/integrations/db/engines/postgres/vector_adapter.py`
- `src/text_to_sql/integrations/db/engines/postgres/vector_store.py`
